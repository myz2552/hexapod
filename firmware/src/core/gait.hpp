#pragma once
//
// Ayak yörüngesi üreteci.
//
// Hız modeli: sabit tempo, hıza göre ölçeklenen adım.
//   Her hızda cfg::CYCLE_TIME saniyede bir tam döngü. Hız ritmi hızlandırarak
//   değil, adımı büyüterek elde edilir: adım = ayak hızı * destek süresi. Gereken
//   en büyük adım erişilebilir max_stride'ı aşarsa, dönüş yarıçapı korunsun diye
//   tüm hareket (doğrusal + açısal birlikte) küçültülür.
//
// Yürüme <-> durma: döngü yalnızca tüm ayaklar yerdeyken durur, başlar veya
//   yürüyüş tipini değiştirir. Sıfır komut önce devam eden salınımların yere
//   inmesine izin verir; yürürken istenen yürüyüş tipi değişikliği robot durana
//   kadar bekler.
//
// Çıktı: ayak hedefleri, bacak başına bir Vec3 (mm). Gövdenin nötr zemin
//   çerçevesindedirler: xy gövde düzleminde, yerdeki ayak için z = 0, salınım
//   ortasında z > 0. Ayakta duruş yüksekliği, gövde eğimi ve gövde kayması burada
//   hesaba katılmaz

#include <cmath>
#include <cstdint>

#include "core/config.hpp"
#include "utils/math.hpp"

namespace gait {

using math::Vec3;

// Yürüyüş tanımlayıcıları. Sıra cfg::GAIT[] ve proto::GaitId ile aynı olmalı ki
// hattan gelen kimlik doğrudan indeks olarak kullanılabilsin. Bu çekirdek dosya
// protokolden bağımsız kalsın diye burada tanımlanır
enum GaitId : uint8_t { TRIPOD = 0, WAVE = 1, RIPPLE = 2, N_GAITS = 3 };

// Bir yürüyüşün fazını bacaklara nasıl dağıttığı: her bacak bir faz grubuna
// aittir ve gruplar döngü boyunca eşit aralıklarla sırayla kalkar.
//
// group_of[leg] == -1, bu yürüyüşe KATILMAYAN bir bacağı işaretler. Klasik üç
// yürüyüş altı bacağın hepsini kullanır, bu yüzden hiçbiri -1 değildir. Yengeç
// yürüyüşü dört bacakla yürür ve diğer ikisini boşta bırakır; ör. ön dört bacaklı
// yengeç (FR, MR, ML, FL bacakları) şöyle olurdu
//     { 2, { 0, 1, -1, -1, 1, 0 } }
// iki arka bacak boşta. Yalnızca tablo değişir; update() mantığı boştaki bacakları
// zaten atlar
// YAPILACAK: yengeç yürüyüşünü gerçekten uygulamamız gerektiğini unutma
struct Pattern {
  uint8_t num_groups;
  int8_t
      group_of[cfg::N_LEGS]; // bacak başına faz grubu, -1 = bu yürüyüşe katılmıyor
};

// Bacak indisi cfg::Leg enum'udur:
//   FRONT_RIGHT=0  MIDDLE_RIGHT=1  REAR_RIGHT=2  REAR_LEFT=3  MIDDLE_LEFT=4
//   FRONT_LEFT=5
constexpr Pattern PATTERN[N_GAITS] = {
    // TRIPOD: sırayla iki üçlü (FR,RR,ML) ve (MR,RL,FL)
    {2, {0, 1, 0, 1, 0, 1}},
    // WAVE: her seferde tek bacak; önce sağ taraf boyunca aşağı, sonra sol taraf boyunca yukarı
    {6, {0, 1, 2, 3, 4, 5}},
    // RIPPLE: üç çapraz çift
    {3, {0, 1, 2, 0, 2, 1}},
};

static_assert(
    sizeof(cfg::GAIT) / sizeof(cfg::GAIT[0]) == N_GAITS,
    "PATTERN[] and cfg::GAIT[] must describe the same gaits in the same order");

class Generator {
public:
  struct Feet {
    Vec3 pos[cfg::N_LEGS];
  };

  Generator() {
    compute_neutral();
    reset();
  }

  // Yürüyüş tipini değiştirmek her bacağın fazını yeniden eşler; yürürken yapılırsa
  // havadaki ayaklar düşer, yerdekiler havaya fırlar. Yürürken istek bekletilir ve
  // robot durunca uygulanır; dururken hemen uygulanır.
  void set_gait(GaitId g) {
    if (walking_) {
      pending_gait_ = g;
      has_pending_ = true;
    } else {
      gait_ = g;
      has_pending_ = false;
      settle_phase();
    }
  }
  GaitId gait() const { return gait_; } // kullanılan yürüyüş (bekleyen değil)

  // Config'ten türetilen önbellekli durumu yeniden hesaplar (nötr duruş cfg::MOUNT ve
  // cfg::STANCE_RADIUS'a bağlıdır). Bunlar yapılandırıldıktan sonra çağrılmalıdır;
  // yürüyüş başına parametreler (duty/adım/...) her update'te cfg::GAIT'ten canlı
  // okunur, onlar için yenileme gerekmez.
  void reconfigure() { compute_neutral(); }

  // Fazı ve update başına durumu temizler. Yeni bir yürüyüşe başlamadan önce çağrılır.
  // Yürürken istenmiş bir yürüyüş tipi yine de geçerli olur
  void reset() {
    phase_ = 0.0f;
    achieved_vx_ = achieved_vy_ = achieved_wz_deg_ = 0.0f;
    walking_ = stopping_ = false;
    stop_left_ = 0.0f;
    if (has_pending_) {
      gait_ = pending_gait_;
      has_pending_ = false;
    }
    settle_phase();
  }

  // Yürüyüşü dt kadar ilerletir ve bu adımın ayak hedeflerini döndürür.
  //   dt         önceki çağrıdan bu yana geçen süre (s)
  //   vx, vy     komut verilen gövde doğrusal hızı (mm/s)
  //   wz_deg     komut verilen yaw hızı (derece/s, +saat yönünün tersi)
  //
  // dt bilerek parametredir: böylece yürüyüşün kendi saati ve döngü frekansı hakkında
  // bir varsayımı olmaz; zamanlama oynasa da tempo doğru kalır ve her şey testte
  // belirlenimci olarak ilerler. Çağıranın komutu önceden kırpmış/yumuşatmış olması
  // beklenir; burada uygulanan tek sınır adım erişilebilirliği sınırıdır
  Feet update(float dt, float vx, float vy, float wz_deg);

  // Son update'te gerçekten uygulanan, kırpma sonrası hareket (odometri için).
  // Adım doymadıkça komutla aynıdır; doyduysa iki bileşen de aynı katsayıyla
  // ölçeklenmiştir (yarıçap korunur)
  float achieved_vx() const { return achieved_vx_; }
  float achieved_vy() const { return achieved_vy_; }
  float achieved_yaw_rate() const { return achieved_wz_deg_; }

  // Sorgular (telemetri/gövde dengelemesi için kullanışlı)
  float phase() const { return phase_; }
  // Döngü çalışırken true'dur; komut sıfıra düştükten sonra biten adımlar da
  // dahildir. Tüm ayaklar yerdeyken donduğunda false olur
  bool walking() const { return walking_; }
  const Vec3 &neutral(int leg) const { return neutral_[leg]; }
  bool in_stance(int leg) const {
    return PATTERN[gait_].group_of[leg] < 0 || leg_phase(leg, phase_) < duty();
  }

private:
  // Yürüyüş başına parametreler, derlenmiş config'ten alınır
  float duty() const { return cfg::GAIT[gait_].duty_factor; }
  float step_height() const { return cfg::GAIT[gait_].step_height; }
  float max_stride() const { return cfg::GAIT[gait_].max_stride; }
  float overlap() const { return cfg::GAIT[gait_].overlap; }

  static float wrap01(float p) { return p - std::floor(p); }

  // Salınımın iki ucuna bu kadar yakın bir salınım (salınım ilerlemesi olarak) yerde
  // sayılır: orada sin^2 kaldırması adım yüksekliğinin %0.12'sinin altındadır. Sınırlardaki
  // float gürültüsünü emer ve salınım pencereleri döngüyü tam dolduran yürüyüşlerin
  // (wave) bir bacak indiği ve bir sonraki henüz kalkmadığı anda durmasını sağlar
  static constexpr float REST_TOL = 0.02f;

  bool airborne(int leg, float global) const {
    if (PATTERN[gait_].group_of[leg] < 0) return false;
    const float lp = leg_phase(leg, global);
    const float s = (lp - duty()) / (1.0f - duty());
    return lp > duty() && s > REST_TOL && s < 1.0f - REST_TOL;
  }

  // Hiçbir ayak havada kalmayana kadar fazın `global`'den ne kadar (döngü cinsinden)
  // ilerlemesi gerektiği: devam eden her salınımın inmesine izin ver, bu arada başlayan
  // salınımlar için tekrarla. Yürüyüşte hiçbir an tüm ayaklar yerde değilse (salınım
  // pencereleri örtüşür, ör. duty < 0.5 olan tripod) -1 döner; bu durumda temiz duramaz
  float rest_distance(float global) const {
    float travelled = 0.0f;
    for (int round = 0; round <= cfg::N_LEGS; ++round) {
      float wait = 0.0f;
      for (int leg = 0; leg < cfg::N_LEGS; ++leg)
        if (airborne(leg, global + travelled))
          wait = std::fmax(wait, 1.0f - leg_phase(leg, global + travelled));
      if (wait == 0.0f) return travelled;
      travelled += wait;
    }
    return -1.0f;
  }

  // Donmuş bir döngüyü bir sonraki tüm ayakların yerde olduğu faza taşır. Yalnızca
  // donmuşken güvenlidir: ayaklar o sırada nötrde park hâlindedir, yani faz yalnızca bir
  // sonraki yürüyüşün başlayacağı yerdir ve yerdeki bir fazdan başlamak hiçbir ayağın
  // havada başlamaması demektir
  void settle_phase() {
    const float d = rest_distance(phase_);
    if (d > 0.0f) phase_ = wrap01(phase_ + d);
  }

  // Nötr (adım ortası, yerde) ayak konumu: montaj noktası bacağın montaj yaw'ı
  // boyunca STANCE_RADIUS kadar dışarı itilir. Bir kez hesaplanır
  void compute_neutral() {
    for (int leg = 0; leg < cfg::N_LEGS; ++leg) {
      const float yaw = math::deg2rad(cfg::MOUNT[leg].yaw_deg);
      neutral_[leg] = {cfg::MOUNT[leg].x + cfg::STANCE_RADIUS * std::cos(yaw),
                       cfg::MOUNT[leg].y + cfg::STANCE_RADIUS * std::sin(yaw),
                       0.0f};
    }
  }

  // Bir bacağın fazı [0,1): [0,duty) destek, [duty,1) salınım
  float leg_phase(int leg, float global) const {
    const Pattern &pat = PATTERN[gait_];
    const float offset =
        float(pat.group_of[leg]) * (1.0f - overlap()) / float(pat.num_groups);
    return wrap01(global + offset);
  }

  // Bu ayağın destek fazında izlemesi gereken zemin hızı: gövdenin doğrusal hızı
  // artı gövde yaw'ından gelen teğetsel hız (omega x r), nötr ayak noktasında
  Vec3 foot_velocity(int leg, float vx, float vy, float wz_rad) const {
    const Vec3 &n = neutral_[leg];
    return {vx - n.y * wz_rad, vy + n.x * wz_rad, 0.0f};
  }

  // Verilen fazdaki bir bacağın ayak konumu, tam destek adımı verildiğinde
  Vec3 foot_position(int leg, float global, const Vec3 &stride) const {
    const Vec3 &n = neutral_[leg];
    const float lp = leg_phase(leg, global);
    const float df = duty();
    if (lp < df) {
      // Destek: yerde, önden (+yarım adım) arkaya (-yarım) kayar
      const float progress = 0.5f - lp / df;
      Vec3 p = n + stride * progress;
      p.z = 0.0f;
      return p;
    }
    // Salınım: havada, arkadan (-yarım) öne (+yarım). Ayak tam bir destek ayağı gibi
    // hareket ederek kalkar ve iner, böylece tripod geçişinde darbe veya sürtünme olmaz:
    // yatayda uç eğimleri destek hızına eşit kübik Hermite (kalktıktan sonra kısa süre
    // geriye devam eder ve yere değerken zaten geriye kayıyordur, adım uçlarını ~%5
    // aşar), dikeyde sin^2; böylece kaldırma sıfır dikey hızla başlar ve biter
    const float s = (lp - df) / (1.0f - df); // salınım boyunca 0..1
    const float m = -(1.0f - df) / df;       // destek eğimi, birim s başına adım cinsinden
    const float s2 = s * s, s3 = s2 * s;
    const float h00 = 2.0f * s3 - 3.0f * s2 + 1.0f, h10 = s3 - 2.0f * s2 + s;
    const float h01 = -2.0f * s3 + 3.0f * s2, h11 = s3 - s2;
    const float progress = -0.5f * h00 + 0.5f * h01 + m * (h10 + h11);
    Vec3 p = n + stride * progress;
    const float lift = std::sin(math::PI * s);
    p.z = step_height() * lift * lift;
    return p;
  }

  GaitId gait_ = TRIPOD;
  float phase_ = 0.0f;
  float achieved_vx_ = 0.0f, achieved_vy_ = 0.0f, achieved_wz_deg_ = 0.0f;
  Vec3 neutral_[cfg::N_LEGS];

  // Yürüme <-> durma geçişi
  bool walking_ = false;     // döngü çalışıyor (ayaklar fazı izler)
  bool stopping_ = false;    // sıfır komut: devam eden salınımlar bitiriliyor
  float stop_left_ = 0.0f;   // tüm ayaklar yere inene kadar daha çalışacak döngü sayısı
  GaitId pending_gait_ = TRIPOD;
  bool has_pending_ = false; // set_gait() yürürken geldi; durunca uygulanır
};

inline Generator::Feet Generator::update(float dt, float vx, float vy,
                                         float wz_deg) {
  const Pattern &pat = PATTERN[gait_];
  const float wz = math::deg2rad(wz_deg);
  const float stance_dur = duty() * cfg::CYCLE_TIME;

  // İzlenecek bacak başına zemin hızı ve bunların en büyüğü
  Vec3 foot_vel[cfg::N_LEGS];
  float max_speed = 0.0f;
  for (int leg = 0; leg < cfg::N_LEGS; ++leg) {
    if (pat.group_of[leg] < 0)
      continue; // boştaki bacak (yengeç): adım yok
    foot_vel[leg] = foot_velocity(leg, vx, vy, wz);
    max_speed = std::fmax(max_speed, foot_vel[leg].norm_xy());
  }

  Vec3 stride[cfg::N_LEGS] = {};
  float twist_scale = 1.0f;
  bool advancing = false;

  if (max_speed > 1e-3f) {
    // Normal yürüyüş. Adım = ayak hızı * destek süresi; en büyük adım erişilebilir
    // kalsın diye kırpılır (tüm hareketi ölçeklemek yarıçapı korur)
    advancing = true;
    float max_needed = 0.0f;
    for (int leg = 0; leg < cfg::N_LEGS; ++leg) {
      if (pat.group_of[leg] < 0)
        continue;
      stride[leg] = foot_vel[leg] * stance_dur;
      max_needed = std::fmax(max_needed, stride[leg].norm_xy());
    }
    if (max_needed > max_stride()) {
      twist_scale = max_stride() / max_needed;
      for (int leg = 0; leg < cfg::N_LEGS; ++leg)
        stride[leg] = stride[leg] * twist_scale;
    }
  }
  // aksi hâlde: sıfır komut, adım sıfır kalır.

  achieved_vx_ = advancing ? vx * twist_scale : 0.0f;
  achieved_vy_ = advancing ? vy * twist_scale : 0.0f;
  achieved_wz_deg_ = advancing ? wz_deg * twist_scale : 0.0f;

  const float step = dt / cfg::CYCLE_TIME;
  if (advancing) {
    // Yürüyor, durağandan başlıyor ya da tamamlanmadan iptal edilmiş bir durma. Döngü
    // her zaman tüm ayakların yerde olduğu bir fazda durur, bu yüzden başlamak hiçbir
    // ayağı salınım ortasında kaldırmaz
    walking_ = true;
    stopping_ = false;
    phase_ = wrap01(phase_ + step);
  } else if (walking_) {
    // Bacaklar hâlâ dönerken sıfır komut. Olduğu yerde donmak havadaki bir ayağı tek
    // adımda yere düşürürdü (ve o fazdan devam etmek onu tekrar yukarı çekerdi); bu
    // yüzden sıfır adımla dönmeye devam et, bu havadaki ayakları nötrde yere indirir;
    // devam eden her salınım indiğinde tam orada don
    if (!stopping_) {
      stopping_ = true;
      stop_left_ = std::fmax(rest_distance(phase_), 0.0f); // -1: şimdi don
    }
    if (step < stop_left_) {
      phase_ = wrap01(phase_ + step);
      stop_left_ -= step;
    } else {
      phase_ = wrap01(phase_ + stop_left_);
      walking_ = stopping_ = false;
      if (has_pending_) {
        gait_ = pending_gait_;
        has_pending_ = false;
        settle_phase();
      }
    }
  }

  Feet out;
  if (!walking_) {
    // Durağan: her ayak nötrde, yerde ve faz donmuş
    for (int leg = 0; leg < cfg::N_LEGS; ++leg)
      out.pos[leg] = neutral_[leg];
    return out;
  }

  for (int leg = 0; leg < cfg::N_LEGS; ++leg) {
    out.pos[leg] = (pat.group_of[leg] < 0)
                       ? neutral_[leg] // boştaki bacak nötrde park edilir
                       : foot_position(leg, phase_, stride[leg]);
  }
  return out;
}

} // namespace gait
