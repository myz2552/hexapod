#pragma once
//
// Robot yöneticisi, HER ŞEYİ yönetir.
//
// Durum makinesi (proto::State). Kalkma/oturma animasyonları kesilemez: bir kez
// başladıklarında sonuna kadar oynarlar. Araya girebilecek tek şey aşırı akım
// hatasıdır; enerjili herhangi bir durumdan robotu durdurur ve enerjiyi keser.
//
//   OFF       enerjisiz, bacaklar katlı, enable() bekliyor. Açılış buradan başlar ve
//             tamamlanan bir oturma buraya döner.
//   SETUP     kalkış: enable() ayağa kalkma animasyonunu çalıştırır (bacakları
//             bulundukları yerden katla -> nötre getir -> gövdeyi kaldır), sonra -> IDLE.
//   IDLE      ayakta, ayaklar nötrde; gövde pozu ara değerlenir. Herhangi bir hız -> WALK.
//   WALK      yürüyüş üreteci sürer; hız sıfıra oturup yürüyüş tüm ayakları yere
//             indirince IDLE'a döner.
//   SHUTDOWN  alçalma: shutdown() oturma animasyonunu çalıştırır (bacaklar nötre ->
//             gövdeyi indir -> bacakları katla, femur maksimuma), sonra gücü keser -> OFF.
//   FAULT     acil durdurma: hemen durdurulur ve enerjisi kesilir (animasyon yok);
//             enerjili her durumdan buraya geçilebilir (yazılımla aşırı akım). enable() toparlar.
//
// Gövde pozu içeride mutlaktır (mm, rad); ayakta duruş == (0, 0, STANDING_HEIGHT).
// set_body_pose() bu referansa göre ofset alır. Açılar yalnızca IK'de radyana çevrilir

#include <cmath>
#include <initializer_list>

#include "core/config.hpp"
#include "utils/math.hpp"
#include "communication/protocol.hpp"
#include "core/gait.hpp"
#include "core/kinematics.hpp"
#include "communication/hardware.hpp"

namespace robot {

using math::Vec3;

// Servo çerçevesine dönüşüm.
//
// Yürüyüş ve gövde pozu komutları zemin çerçevesinde ayak hedefleri üretir. Bu
// katman eyleyicilere giden geometrik bağdır: her bacak için IK'yi çalıştırır
// (komut verilen gövde pozunu da hesaba katarak) ve çıkan kinematik açıları
// config.hpp'deki eklem başına kalibrasyon verisiyle servo uzayına eşler.
//
//   ayak hedefleri (+ gövde pozu) -> IK -> kinematik açılar (rad) -> kalibrasyon -> servo derecesi

// cfg::servo_channel(leg, joint) ile indekslenen, derece cinsinden 18 servo açısı
struct ServoAngles {
  float deg[cfg::N_SERVOS];
};

// Kinematik açı (rad) -> servo açısı (derece), config kalibrasyonuna göre:
//   servo_deg = clamp(kin_deg * direction + trim, min, max)
// direction/trim servo başınadır (bacak öncelikli); kırpma eklem tipi başınadır.
inline float map_servo(int leg, int joint, float kin_rad) {
  const int ch = cfg::servo_channel(leg, joint);
  const float deg = math::rad2deg(kin_rad) * cfg::DIRECTION[ch] + cfg::TRIM_DEG[ch];
  return math::clampf(deg, cfg::RANGE[joint].min_deg, cfg::RANGE[joint].max_deg);
}

// map_servo'nun tersi, kırpma yok sayılarak: servo açısı (derece) -> kinematik (rad).
// Ölçülen servo konumlarından FK başlatmak için kullanışlıdır
inline float unmap_servo(int leg, int joint, float servo_deg) {
  const int ch = cfg::servo_channel(leg, joint);
  return math::deg2rad((servo_deg - cfg::TRIM_DEG[ch]) / cfg::DIRECTION[ch]);
}

// Bir adımın ayak hedeflerini servo açılarına çevirir. body_pos/body_rpy, zemin
// çerçevesinde komut verilen gövde pozudur (body_pos.z ayakta duruş yüksekliğini
// taşır). Herhangi bir bacağın hedefi geometrik olarak erişilemezse false döner;
// o durumda o bacağın açıları anlamsızdır ve çağıran bunu uygulamak yerine önceki
// komutu korumalıdır
inline bool resolve(const Vec3 (&feet)[cfg::N_LEGS], const Vec3 &body_pos,
                    const Vec3 &body_rpy, ServoAngles &out) {
  bool ok = true;
  for (int leg = 0; leg < cfg::N_LEGS; ++leg) {
    const kin::IkResult r = kin::inverse(leg, feet[leg], body_pos, body_rpy);
    if (!r.ok)
      ok = false;
    out.deg[cfg::servo_channel(leg, cfg::COXA)] = map_servo(leg, cfg::COXA, r.coxa);
    out.deg[cfg::servo_channel(leg, cfg::FEMUR)] = map_servo(leg, cfg::FEMUR, r.femur);
    out.deg[cfg::servo_channel(leg, cfg::TIBIA)] = map_servo(leg, cfg::TIBIA, r.tibia);
  }
  return ok;
}

class Robot {
public:
  explicit Robot(hw::Interface &hw) : hw_(hw) {
    hw_.set_power(false);
    // Servo sıfırında değil, katlı dinlen: sıfır keyfi bir servo okumasıdır ve katlı
    // görünüp görünmemesi tamamen bacağın şekline bağlıdır. HAL'e de yazılır; böylece
    // geri okuma dinlenme pozunu görür ve güç hattı en son hatta ne varsa ona değil,
    // bu poza enerjilenir
    set_curl_pose(servos_);
    hw_.write_servos(servos_.deg);
  }

  // Niyet API'si (yönlendirici çağırır). Her biri bağlantıyı canlı işaretler (watchdog'u besler)

  // Ayağa kalk. Yalnızca enerjisiz bir dinlenme durumundan izinlidir: OFF (açılış ya
  // da tamamen oturmuş) veya FAULT. Animasyon sırasında yok sayılır; böylece kalkma/oturma
  // her zaman sonuna kadar çalışır.
  void enable() {
    pet();
    if (state_ == proto::State::OFF || state_ == proto::State::FAULT)
      start_stand_up();
  }

  // Düzenli kapanış: oturma animasyonu, sonra gücü kes. Yalnızca IDLE/WALK'tan;
  // böylece devam eden bir ayağa kalkmayı kesemez.
  void shutdown() {
    pet();
    if (state_ == proto::State::IDLE || state_ == proto::State::WALK)
      start_sit_down();
  }

  // Yumuşak durma: hızı sıfırla, ayakta kal
  void stop() {
    pet();
    if (state_ == proto::State::IDLE || state_ == proto::State::WALK)
      tvx_ = tvy_ = twz_ = 0.0f;
  }

  void set_velocity(float vx, float vy, float wz) {
    pet();
    if (state_ != proto::State::IDLE && state_ != proto::State::WALK) return;
    tvx_ = math::clampf(vx, -cfg::LIN_VEL_MAX, cfg::LIN_VEL_MAX);
    tvy_ = math::clampf(vy, -cfg::LIN_VEL_MAX, cfg::LIN_VEL_MAX);
    twz_ = math::clampf(wz, -cfg::ANG_VEL_MAX, cfg::ANG_VEL_MAX);
  }

  void set_body_pose(float x, float y, float z, float roll, float pitch,
                     float yaw) {
    pet();
    if (state_ != proto::State::IDLE && state_ != proto::State::WALK) return;
    const cfg::BodyPoseLimits &L = cfg::BODY_POSE;
    body_pos_t_ = {math::clampf(x, L.x_min, L.x_max),
                   math::clampf(y, L.y_min, L.y_max),
                   cfg::STANDING_HEIGHT + math::clampf(z, L.z_min, L.z_max)};
    body_rpy_t_ = {math::deg2rad(math::clampf(roll, L.roll_min, L.roll_max)),
                   math::deg2rad(math::clampf(pitch, L.pitch_min, L.pitch_max)),
                   math::deg2rad(math::clampf(yaw, L.yaw_min, L.yaw_max))};
  }

  void set_gait(gait::GaitId g) { pet(); gait_.set_gait(g); }

  void set_led(uint8_t mode, uint8_t r, uint8_t g, uint8_t b, float freq_hz) {
    pet();
    hw_.set_led(mode, r, g, b, freq_hz);
  }

  void heartbeat() { pet(); }

  // Yapılandırma desteği (yönlendirici çağırır). Config ve kalibrasyon jog'una yalnızca
  // enerji yokken izin verilir; böylece hareket sırasında hiçbir şey yeniden
  // yapılandırılmaz veya ham servo sürülmez. Pi, enable()'dan önce, bağlanırken yapılandırır.
  bool provisionable() const {
    return state_ == proto::State::OFF || state_ == proto::State::FAULT;
  }
  // Geometri (montajlar/duruş) veya servo eşlemesi yapılandırıldıktan sonra config'ten
  // türetilen önbellekli durumu yeniden hesaplar. Enerji yokken komut verilen poz
  // dinlenme pozunun KENDİSİDİR ve onu tanımlayan şey yapılandırılan config'tir, bu
  // yüzden o da güncellenir.
  void reconfigure() {
    gait_.reconfigure();
    if (!energized_) {
      set_curl_pose(servos_);
      hw_.write_servos(servos_.deg);
    }
  }
  // Fiziksel yapılandırma / kalibrasyon jog'u HAL'dedir.
  void set_servo_calibration(uint8_t ch, uint16_t min_us, uint16_t mid_us,
                             uint16_t max_us) {
    hw_.set_servo_calibration(ch, min_us, mid_us, max_us);
  }
  void set_servo_pin(uint8_t ch, uint8_t pin) { hw_.set_servo_pin(ch, pin); }
  void jog_servo(uint8_t ch, uint16_t pulse_us) { hw_.jog_servo(ch, pulse_us); }

  // Periyodik adım (kontrol döngüsü ~CONTROL_RATE_HZ hızında çağırır)
  void update(float dt) {
    hw_.update_leds(); // LED animasyonu kartındır; burada yalnızca ilerletiyoruz

    voltage_ = hw_.read_voltage();
    current_ = hw_.read_current();

    // Aşırı akım, enerjili HER durumdan acil durdurmayı tetikler: motorlara giden fazla
    // akım her zaman gerçek bir hatadır. Düşük voltaj tek başına hata DEĞİLDİR; böylece
    // kart motor hattı kapalıyken de çalışır (masa testleri, simülasyon): voltaj ölçümü
    // ~0 okur ve robot yalnızca hareket ettiğini sanır
    if (energized_ && current_ > cfg::CURRENT_MAX) {
      trip_fault();
      return;
    }

    switch (state_) {
      case proto::State::SETUP:    // kalkış  : sonuna kadar oynar (hata dışında)
      case proto::State::SHUTDOWN: // alçalma: sonuna kadar oynar (hata dışında)
        run_sequencer(dt);
        break;
      case proto::State::IDLE:
      case proto::State::WALK:
        run_active(dt);
        break;
      case proto::State::OFF:   // enerjisiz bekleme; enable()'a kadar yapılacak bir şey yok
      case proto::State::FAULT: // durdurulmuş ve enerjisiz; enable()'a kadar böyle kalır
        break;
    }
  }

  // Sorgular (yanıtlar/telemetri için)
  proto::State state() const { return state_; }
  float voltage() const { return voltage_; }
  float current() const { return current_; }
  void odometry(float &x, float &y, float &yaw_rad) const {
    x = odom_x_;
    y = odom_y_;
    yaw_rad = odom_yaw_;
  }
  const ServoAngles &joints() const { return servos_; }
  
  // Canlı gövde pozu (hedef değil, ilerleme sırasındaki ara değer), set_body_pose ile
  // aynı birim/referansta: x/y/z mm, z ayakta duruş yüksekliğine göre, roll/pitch/yaw derece.
  void body_pose(float &x, float &y, float &z, float &roll, float &pitch,
                 float &yaw) const {
    x = body_pos_.x;
    y = body_pos_.y;
    z = body_pos_.z - cfg::STANDING_HEIGHT;
    roll = math::rad2deg(body_rpy_.x);
    pitch = math::rad2deg(body_rpy_.y);
    yaw = math::rad2deg(body_rpy_.z);
  }

private:
  static constexpr float VEL_DEADBAND = 0.5f; // mm/s  : bunun altında yumuşatılmış v'yi 0'a sabitle
  static constexpr float ANG_DEADBAND = 0.3f; // derece/s
  enum class Step : uint8_t { Curl, LegsToNeutral, RaiseBody, LowerBody };

  void pet() { since_cmd_ = 0.0f; }

  // IDLE / WALK
  void run_active(float dt) {
    since_cmd_ += dt;
    // Haberleşme koptu: torku sonsuza kadar tutmak yerine otur ve gücü kes (OFF'ta biter, yani kalkmak için bağlantı tekrar enable göndermeli)
    if (since_cmd_ > cfg::WATCHDOG_TIMEOUT_MS / 1000.0f) {
      start_sit_down();
      return;
    }

    smooth_commands(dt);
    slew_body(dt); // komut verilen gövde pozuna doğru

    const gait::Generator::Feet feet = gait_.update(dt, cvx_, cvy_, cwz_);
    for (int leg = 0; leg < cfg::N_LEGS; ++leg) leg_[leg] = feet.pos[leg];
    resolve_write();
    integrate_odometry(dt);

    // Durdurulduktan sonra yürüyüş devam eden adımları bitirirken hâlâ WALK
    const bool moving = tvx_ != 0.0f || tvy_ != 0.0f || twz_ != 0.0f ||
                        cvx_ != 0.0f || cvy_ != 0.0f || cwz_ != 0.0f ||
                        gait_.walking();
    state_ = moving ? proto::State::WALK : proto::State::IDLE;
  }

  // SETUP / SHUTDOWN sıralayıcısı
  void run_sequencer(float dt) {
    if (run_step(seq_[seq_idx_], dt)) {
      ++seq_idx_;
      if (seq_idx_ >= seq_len_) finalize_sequence();
    }
  }

  bool run_step(Step s, float dt) {
    switch (s) {
    case Step::Curl:
      return curl_step(dt);
    case Step::LegsToNeutral: {
      for (int leg = 0; leg < cfg::N_LEGS; ++leg) leg_t_[leg] = gait_.neutral(leg);
      const bool done = slew_legs(dt);
      resolve_write();
      return done;
    }
    case Step::RaiseBody:
      body_pos_t_ = {0.0f, 0.0f, cfg::STANDING_HEIGHT};
      body_rpy_t_ = {};
      { const bool done = slew_body(dt); resolve_write(); return done; }
    case Step::LowerBody:
      body_pos_t_ = {};
      body_rpy_t_ = {};
      { const bool done = slew_body(dt); resolve_write(); return done; }
    }
    return true;
  }

  void finalize_sequence() {
    if (post_seq_ == proto::State::IDLE) { // ayağa kalkma bitti -> ayakta
      gait_.reset();
      reset_motion();
      body_pos_t_ = {0.0f, 0.0f, cfg::STANDING_HEIGHT};
      body_rpy_t_ = {};
      state_ = proto::State::IDLE;
    } else { // oturma bitti: bacaklar katlı -> gücü kes ve OFF'ta dinlen
      hw_.set_power(false);
      energized_ = false;
      state_ = proto::State::OFF;
    }
  }

  void start_stand_up() {
    hw_.set_power(true);
    energized_ = true;
    reset_motion();
    gait_.reset();
    body_pos_ = {};   body_pos_t_ = {};   // gövde yerdeyken başla
    body_rpy_ = {};   body_rpy_t_ = {};
    // Bacakların GERÇEKTE bulunduğu yerden başla: servo açılarını karttan geri oku ve
    // FK ile Kartezyen ayak durumunu çıkar. Ardından Curl adımı bacakları gerçek
    // başlangıç pozlarından katlar ("zaten katlı" varsayımı yok).
    hw_.read_servos(servos_.deg);
    seed_legs_from_servos();
    begin_sequence({Step::Curl, Step::LegsToNeutral, Step::RaiseBody},
                   proto::State::IDLE);
    state_ = proto::State::SETUP;
  }

  void start_sit_down() {
    tvx_ = tvy_ = twz_ = 0.0f;
    cvx_ = cvy_ = cwz_ = 0.0f;
    begin_sequence({Step::LegsToNeutral, Step::LowerBody, Step::Curl},
                   proto::State::OFF);
    state_ = proto::State::SHUTDOWN;
  }

  // Acil durdurma: hareketi ve gücü hemen kes; enable() ile toparlanır.
  void trip_fault() {
    tvx_ = tvy_ = twz_ = 0.0f;
    cvx_ = cvy_ = cwz_ = 0.0f;
    hw_.set_power(false);
    energized_ = false;
    seq_len_ = seq_idx_ = 0;
    state_ = proto::State::FAULT;
  }

  // animasyon temel işlemleri

  // Bacakları güvenli kapanma pozuna katlar (femur/tibia servo maksimumlarında), servo
  // uzayında JOINT_VEL_MAX hızında ara değerleyerek. Katlandıktan sonra Kartezyen ayak
  // durumunu FK'den başlatır; böylece sonraki LegsToNeutral adımı gerçek durumdan başlar.
  bool curl_step(float dt) {
    ServoAngles target;
    set_curl_pose(target);
    const float step = cfg::JOINT_VEL_MAX * dt;
    bool done = true;
    for (int leg = 0; leg < cfg::N_LEGS; ++leg) {
      float *cur = &servos_.deg[cfg::servo_channel(leg, 0)];
      const float *tgt = &target.deg[cfg::servo_channel(leg, 0)];
      const float ex = tgt[0] - cur[0], ey = tgt[1] - cur[1], ez = tgt[2] - cur[2];
      const float d = std::sqrt(ex * ex + ey * ey + ez * ez);
      if (d > step) {
        const float k = step / d;
        cur[0] += ex * k; cur[1] += ey * k; cur[2] += ez * k;
        done = false;
      } else {
        cur[0] = tgt[0]; cur[1] = tgt[1]; cur[2] = tgt[2];
      }
    }
    hw_.write_servos(servos_.deg);
    if (done) seed_legs_from_servos();
    return done;
  }

  // Her ayağın hedefine doğru hız sınırlı Kartezyen hareketi (mm/s).
  bool slew_legs(float dt) {
    const float step = cfg::BODY_LIN_VEL_MAX * dt;
    bool done = true;
    for (int leg = 0; leg < cfg::N_LEGS; ++leg) {
      const Vec3 err = leg_t_[leg] - leg_[leg];
      const float d = err.norm();
      if (d > step) { leg_[leg] += err * (step / d); done = false; }
      else          { leg_[leg] = leg_t_[leg]; }
    }
    return done;
  }

  // Gövde pozunun hedefine doğru hız sınırlı hareketi (konum mm/s, yönelim derece/s).
  bool slew_body(float dt) {
    bool done = true;
    const Vec3 perr = body_pos_t_ - body_pos_;
    const float pm = perr.norm();
    const float lin = cfg::BODY_LIN_VEL_MAX * dt;
    if (pm > lin) { body_pos_ += perr * (lin / pm); done = false; }
    else          { body_pos_ = body_pos_t_; }

    Vec3 oerr = body_rpy_t_ - body_rpy_;
    oerr.z = math::wrap_angle(oerr.z);
    const float om = oerr.norm();
    const float ang = math::deg2rad(cfg::BODY_ANG_VEL_MAX) * dt;
    if (om > ang) { body_rpy_ += oerr * (ang / om); done = false; }
    else          { body_rpy_ = body_rpy_t_; }
    return done;
  }

  // yardımcılar

  void resolve_write() {
    ServoAngles next;
    if (resolve(leg_, body_pos_, body_rpy_, next))
      servos_ = next; // aksi hâlde ileri atılmak yerine son iyi pozu koru
    hw_.write_servos(servos_.deg);
  }

  // Servo derecesi cinsinden güvenli katlı poz: coxa nötr, femur ve tibia maksimumlarında.
  static void set_curl_pose(ServoAngles &s) {
    for (int leg = 0; leg < cfg::N_LEGS; ++leg) {
      s.deg[cfg::servo_channel(leg, cfg::COXA)] = map_servo(leg, cfg::COXA, 0.0f);
      s.deg[cfg::servo_channel(leg, cfg::FEMUR)] = cfg::RANGE[cfg::FEMUR].max_deg;
      s.deg[cfg::servo_channel(leg, cfg::TIBIA)] = cfg::RANGE[cfg::TIBIA].max_deg;
    }
  }

  // Mevcut servo açılarından gövde çerçevesinde ayak konumları (ters eşlenmiş
  // kinematik açıların FK'si).
  void seed_legs_from_servos() {
    for (int leg = 0; leg < cfg::N_LEGS; ++leg) {
      const float c = unmap_servo(leg, cfg::COXA,  servos_.deg[cfg::servo_channel(leg, cfg::COXA)]);
      const float f = unmap_servo(leg, cfg::FEMUR, servos_.deg[cfg::servo_channel(leg, cfg::FEMUR)]);
      const float t = unmap_servo(leg, cfg::TIBIA, servos_.deg[cfg::servo_channel(leg, cfg::TIBIA)]);
      leg_[leg] = kin::forward(leg, c, f, t, body_pos_, body_rpy_, false);
    }
  }

  void begin_sequence(std::initializer_list<Step> steps, proto::State post) {
    uint8_t i = 0;
    for (Step s : steps) seq_[i++] = s;
    seq_len_ = i;
    seq_idx_ = 0;
    post_seq_ = post;
  }

  void reset_motion() {
    tvx_ = tvy_ = twz_ = 0.0f;
    cvx_ = cvy_ = cwz_ = 0.0f;
    odom_x_ = odom_y_ = odom_yaw_ = 0.0f;
    since_cmd_ = 0.0f;
  }

  // Birinci dereceden alçak geçiren filtre (alpha = dt/(tau+dt), eski kontrolcüdeki
  // gibi), ölü bantla; böylece sıfır komut TAM sıfıra oturur ve yürüyüş donabilir.
  void smooth_commands(float dt) {
    const float a = dt / (cfg::VEL_SMOOTH_TAU + dt);
    cvx_ += a * (tvx_ - cvx_);
    cvy_ += a * (tvy_ - cvy_);
    cwz_ += a * (twz_ - cwz_);
    if (tvx_ == 0.0f && std::fabs(cvx_) < VEL_DEADBAND) cvx_ = 0.0f;
    if (tvy_ == 0.0f && std::fabs(cvy_) < VEL_DEADBAND) cvy_ = 0.0f;
    if (twz_ == 0.0f && std::fabs(cwz_) < ANG_DEADBAND) cwz_ = 0.0f;
  }

  // Yürüyüşün GERÇEKLEŞEN (kırpma sonrası) hareketini dünya pozuna entegre eder. Kural
  // protokolle aynıdır: +x ileri, +y sol, +yaw saat yönünün tersi (sağ el kuralı).
  void integrate_odometry(float dt) {
    odom_yaw_ += math::deg2rad(gait_.achieved_yaw_rate()) * dt;
    const float c = std::cos(odom_yaw_), s = std::sin(odom_yaw_);
    const float vx = gait_.achieved_vx(), vy = gait_.achieved_vy();
    odom_x_ += (c * vx - s * vy) * dt;
    odom_y_ += (s * vx + c * vy) * dt;
  }

  hw::Interface &hw_;
  proto::State state_ = proto::State::OFF; // açılış: enerjisiz bekleme
  bool energized_ = false;
  gait::Generator gait_;

  // Hız komutu hedefleri / yumuşatılmış değerler.
  float tvx_ = 0.0f, tvy_ = 0.0f, twz_ = 0.0f; // mm/s, mm/s, deg/s
  float cvx_ = 0.0f, cvy_ = 0.0f, cwz_ = 0.0f;

  // Gövde pozu (mutlak) + hedefler: konum mm, rpy rad.
  Vec3 body_pos_{}, body_rpy_{};
  Vec3 body_pos_t_{}, body_rpy_t_{};

  // Ayak hedefleri (gövde çerçevesi): mevcut + Kartezyen ilerleme hedefi (animasyonlar).
  Vec3 leg_[cfg::N_LEGS];
  Vec3 leg_t_[cfg::N_LEGS];

  ServoAngles servos_{}; // son komut (aynı zamanda katlama ara değer durumu)

  // Sıralayıcı.
  Step seq_[4] = {};
  uint8_t seq_len_ = 0, seq_idx_ = 0;
  proto::State post_seq_ = proto::State::IDLE;

  // Telemetri / güvenlik.
  float voltage_ = 0.0f, current_ = 0.0f;
  float odom_x_ = 0.0f, odom_y_ = 0.0f, odom_yaw_ = 0.0f; // mm, mm, rad
  float since_cmd_ = 0.0f;                                 // s (watchdog)
};

} // namespace robot
