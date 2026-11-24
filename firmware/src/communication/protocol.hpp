#pragma once
//
// Raspberry Pi ile Servo2040 arasındaki mesajlaşmayı tanımlayan protokol.
// Python arayüzü bu dosyayı elle kopyalar.
//
// Çerçeve düzeni
//
//     ┌──────┬──────┬────────┬───────────────┬──────────┬──────────┐
//     │ SOF  │ LEN  │ opcode │ payload[LEN]  │ CRC lo   │ CRC hi   │
//     │ 0xAA │ 0..N │ 1 bayt │ LEN bayt      │          │          │
//     └──────┴──────┴────────┴───────────────┴──────────┴──────────┘
//
//   - SOF: çerçeve başlangıç işareti (0xAA)
//   - LEN: bayt cinsinden yük uzunluğu (0..MAX_PAYLOAD); opcode SAYILMAZ
//   - CRC: CRC16-CCITT (polinom 0x1021, başlangıç 0xFFFF), little-endian;
//          LEN + opcode + yük üzerinden hesaplanır (böylece uzunluk alanı da korunur)
//   - Toplam: çerçeve boyutu = LEN + 5. Çerçeve sonu baytı yoktur: çerçeveyi LEN
//          sınırlar, CRC doğrular. CRC hatalıysa (veya LEN > MAX_PAYLOAD) alıcı
//          çerçeveyi atar ve bir sonraki SOF'u arar
//
// Çok baytlı tüm alanlar little-endian'dır; float'lar IEEE-754'tür.
// vx = 1.0 float değerini ele alalım. IEEE-754'te 32 biti 0x3F800000'dır.
// Bu 4 bayt iki şekilde sıralanabilir:
//
//   - little-endian (en düşük anlamlı bayt önce):   00 00 80 3F
//   - big-endian    (en yüksek anlamlı bayt önce):  3F 80 00 00
//
// UART düz bir bayt akışı gönderir. İki uç sıra konusunda anlaşamazsa alıcı
// anlamsız veri birleştirir.
// İki kart da little-endian ARM'dir, bu yüzden yük struct'ları doğrudan memcpy ile kopyalanır.
//
// Mesajlar şunlar olabilir:
//
//   - Yanıtsız: yanıt yok. Komut watchdog'unu besler. Hedef değerler/komutlar
//   - İstek/yanıt: aynı opcode'u taşıyan tam olarak bir yanıt çerçevesi
//
// kind_of() bunu kodlar; böylece hem Servo2040 hem Pi yanıt beklemeleri
// gerekip gerekmediğini belirleyebilir

#include <cstddef>
#include <cstdint>

#include "core/config.hpp"

namespace proto {

// Ortak enum'lar (bu değerler hatta taşınır)
//
// Yaşam döngüsü: OFF --Enable--> SETUP --> IDLE <--> WALK --Shutdown--> SHUTDOWN --> OFF
//                enerjili herhangi bir durum --aşırı akım/düşük voltaj--> FAULT --Enable--> SETUP
// SETUP (kalkış) ve SHUTDOWN (alçalma) kesilemeyen animasyonlardır; yalnızca bir
// hata araya girebilir. OFF sona eklenmiştir (değer 5), böylece 0..4 hat değerleri değişmez.
enum class State : uint8_t {
  SETUP = 0,    // RISING: ayağa kalkma animasyonu çalışıyor (enerjisiz dinlenme OFF'tur)
  IDLE = 1,     // ayakta, sıfır hız
  WALK = 2,     // yürüyüş uyguluyor
  SHUTDOWN = 3, // LOWERING: oturma animasyonu çalışıyor
  FAULT = 4,    // acil durdurulmuş: durdurulmuş ve enerjisiz, toparlanmak için Enable gerekir
  OFF = 5,      // enerjisiz bekleme: yeni açılmış ya da tamamen oturmuş, Enable bekliyor
};

enum class GaitId : uint8_t {
  TRIPOD = 0,
  WAVE = 1,
  RIPPLE = 2,
};

enum class LedMode : uint8_t {
  SOLID = 0,
  BLINK = 1,
};

// Yanıt yüklerinde / hata çerçevelerinde döndürülen durum kodları
enum class Status : uint8_t {
  REJECTED = 0x00, // anlaşıldı ama reddedildi (yanlış durum vb.)
  OK = 0x01,
  UNREACHABLE = 0x02, // IK hedefi erişim dışında
  BAD_OPCODE = 0x03,  // bilinmeyen opcode
  BAD_LENGTH = 0x04,  // yük boyutu bu opcode için beklenenden farklı
};

// Opcode'lar
// Okunabilirlik için üst dört bit türe göre gruplar:
//   0x0x  düşük seviye servo/LED hata ayıklama (istek/yanıt, onay)
//   0x1x  yapılandırma / çalışma zamanı ayarları (istek/yanıt, onay)
//   0x3x  yanıtsız hedef değerler / komutlar
//   0x4x  istek/yanıt sorguları
//   0xEE  kartın başlattığı hata yanıtı
//
// Yapılandırma ve jog istek/yanıttır: kart uygular ve AYNI opcode ile bir
// AckReply(Status::OK) döndürür; reddederse (yanlış durum) veya uzunluk hatalıysa
// Error çerçevesi döndürür. Hareket sırasında hiçbir şey yeniden yapılandırılmasın
// diye yalnızca enerji yokken (OFF/FAULT) kabul edilirler; Pi, enable()'dan önce,
// bağlanırken yapılandırır. (0x0x/0x1x/0x2x ileride hata ayıklama/ayar için ayrılmıştır.)
enum class Opcode : uint8_t {
  // düşük seviye hata ayıklama (0x0x)
  JogServo = 0x01, // JogServoMsg -> AckReply  (tek servoya ham darbe)

  // yapılandırma / çalışma zamanı ayarları (0x1x) -> AckReply
  ProvisionBody = 0x10,      // ProvisionBodyMsg       bacak geometrisi, yükseklikler, tempo
  ProvisionMounts = 0x11,    // ProvisionMountsMsg     bacak başına montaj pozu (x, y, z, yaw)
  ProvisionDirection = 0x12, // ProvisionDirectionMsg  servo başına yön (+/-1)
  ProvisionTrim = 0x13,      // ProvisionTrimMsg       servo başına trim (derece)
  ProvisionRanges = 0x14,    // ProvisionRangesMsg     eklem tipi başına servo kırpması
  ProvisionGaits = 0x15,     // ProvisionGaitsMsg      yürüyüş başına parametreler
  ProvisionLimits = 0x16,    // ProvisionLimitsMsg     komut sınırları + aşırı akım
  ProvisionBodyPose = 0x17,  // ProvisionBodyPoseMsg   gövde pozu sınırları
  ProvisionServoCal = 0x18,  // ProvisionServoCalMsg   servo başına [min,orta,max] us (HAL)
  ProvisionPins = 0x19,      // ProvisionPinsMsg       mantıksal->fiziksel pin eşlemesi (HAL)

  // yanıtsız (yanıt yok; watchdog'u besler)
  SetVelocity = 0x30, // SetVelocityMsg
  SetBodyPose = 0x31, // SetBodyPoseMsg
  SetGait = 0x32,     // SetGaitMsg
  Enable = 0x33,      // (yük yok) ayağa kalkma sırasını çalıştır -> IDLE
  Shutdown = 0x34,    // (yük yok) oturma sırasını çalıştır -> SETUP
  Stop = 0x35,        // (yük yok) hızı sıfırla (yumuşak durma)
  SetLed = 0x36,      // SetLedMsg
  Heartbeat = 0x37,   // (yük yok) canlı tutma, watchdog'u besler

  // istek/yanıt (kart aynı opcode ile yanıtlar)
  GetTelemetry = 0x40, // ()           -> TelemetryReply
  GetVoltage = 0x41,   // ()           -> VoltageReply
  GetCurrent = 0x42,   // ()           -> CurrentReply
  GetJoints = 0x43,    // ()           -> JointsReply
  GetBodyPose = 0x44,  // ()           -> BodyPoseReply

  // kartın başlattığı
  Error = 0xEE, // ErrorReply
};

enum class Kind : uint8_t { FireAndForget, RequestReply };

// Bu opcode hangi türden. Bilinmeyen opcode'lar varsayılan olarak RequestReply
// sayılır; böylece yönlendirici sessizce atmak yerine Error çerçevesiyle yanıt verebilir
constexpr Kind kind_of(Opcode op) {
  switch (op) {
  case Opcode::SetVelocity:
  case Opcode::SetBodyPose:
  case Opcode::SetGait:
  case Opcode::Enable:
  case Opcode::Shutdown:
  case Opcode::Stop:
  case Opcode::SetLed:
  case Opcode::Heartbeat:
    return Kind::FireAndForget;
  default:
    return Kind::RequestReply;
  }
}

// Yükler
// Dolgu olmadan sizeof() == hattaki boyut olsun diye sıkıştırılmıştır. Sondaki
// static_assert'ler bu boyutları sabitler
#pragma pack(push, 1)

// Komutlar ("py: <..." Pi'nin kullanması gereken Python struct formatıdır, "<"
// little-endian demektir)

struct SetVelocityMsg { // py: "<fff"
  float vx;             // mm/s, gövde +x (ileri)
  float vy;             // mm/s, gövde +y (sol)
  float wz;             // derece/s, yaw (+ = saat yönünün tersi)
};

struct SetBodyPoseMsg {   // py: "<ffffff"
  float x, y, z;          // mm, gövde kayması (z ayakta duruş yüksekliğine göre)
  float roll, pitch, yaw; // derece
};

struct SetGaitMsg { // py: "<B"
  uint8_t gait_id;  // proto::GaitId
};

struct SetLedMsg { // py: "<BBBBf"
  uint8_t mode;    // proto::LedMode
  uint8_t r, g, b;
  float freq_hz; // yanıp sönme frekansı (mode == BLINK)
};

// Düşük seviye hata ayıklama: tek bir servoyu ham bir darbeye sürer (kalibrasyon
// jog'u). Durum makinesini/yürüyüşü atlar; gerektiğinde güç hattını açar.
// pulse_us == 0 o kanalı bırakır (devre dışı bırakır).
struct JogServoMsg { // py: "<BH"
  uint8_t channel;   // mantıksal kanal, cfg::servo_channel(leg, joint)
  uint16_t pulse_us; // 0 = bırak
};

// Yapılandırma: Pi bağlanırken tüm çalışma zamanı config'ini her mesajda bir
// bölüm olarak gönderir. Yalnızca enerji yokken uygulanır. Diziler config
// düzenine uysun diye bacak öncelikli / eklem önceliklidir.
struct ProvisionBodyMsg { // py: "<fffffff"
  float coxa_len, femur_len, tibia_len; // mm
  float coxa_offset;                    // mm, bacak düzleminin coxa ekseninden kayması
  float standing_height;                // mm
  float stance_radius;                  // mm
  float cycle_time;                     // s
};

struct ProvisionMountsMsg {          // py: "<24f"  bacak başına: x, y, z, yaw_derece
  float mount[cfg::N_LEGS][4];       // [leg] = {x mm, y mm, z mm, yaw deg}
};

// Servo-kinematik eşleme, config YAML'ına uysun diye bölünmüştür: yön ve trim
// servo başınadır (bacak öncelikli, cfg::servo_channel sırası); kırpma eklem tipi başınadır.
struct ProvisionDirectionMsg {       // py: "<18f"  servo başına: yön (+/-1)
  float direction[cfg::N_SERVOS];
};

struct ProvisionTrimMsg {            // py: "<18f"  servo başına: trim_derece
  float trim_deg[cfg::N_SERVOS];
};

struct ProvisionRangesMsg {          // py: "<6f"  eklem tipi başına: min_derece, max_derece
  float range[cfg::N_JOINTS][2];     // [joint] = {min_deg, max_deg}
};

struct ProvisionGaitsMsg {           // py: "<12f"  yürüyüş başına: duty, adım_yüksekliği, adım, örtüşme
  float gait[3][4];                  // [gait] = {duty_factor, step_height, max_stride, overlap}
};

struct ProvisionLimitsMsg { // py: "<ffffffff"
  float lin_vel_max, ang_vel_max, vel_smooth_tau;
  float body_lin_vel_max, body_ang_vel_max, joint_vel_max;
  float current_max;          // A, aşırı akım kesmesi
  float voltage_min;          // V, düşük voltaj kesmesi
};

struct ProvisionBodyPoseMsg { // py: "<12f"  eksen başına: min, max
  float x_min, x_max;         // mm
  float y_min, y_max;         // mm
  float z_min, z_max;         // mm, ayakta duruş yüksekliğine göre
  float roll_min, roll_max;   // derece
  float pitch_min, pitch_max; // derece
  float yaw_min, yaw_max;     // derece
};

struct ProvisionServoCalMsg {          // py: "<54H"  servo başına: min, orta, max (us)
  uint16_t pulse[cfg::N_SERVOS][3];    // [channel] = {min_us, mid_us, max_us}
};

struct ProvisionPinsMsg {           // py: "<18B"  mantıksal kanal başına fiziksel pin
  uint8_t pin[cfg::N_SERVOS];
};

// Yanıtlar

struct TelemetryReply { // py: "<Bfffff"
  uint8_t state;        // proto::State
  float odom_x;         // mm
  float odom_y;         // mm
  float odom_yaw;       // derece
  float voltage;        // V
  float current;        // A
};

struct VoltageReply { // py: "<f"
  float voltage;      // V
};

struct CurrentReply { // py: "<f"
  float current;      // A
};

struct JointsReply {          // py: "<18f"
  float angle[cfg::N_SERVOS]; // servo uzayı derecesi, bacak öncelikli (bacak*3 + eklem)
};

// Canlı gövde pozu: kartın doğru ilerlediği ara değer.
// SetBodyPoseMsg ile aynı düzen/birimler; böylece set/get gidiş-dönüşü tutarlıdır
// (z ayakta duruş yüksekliğine göre).
struct BodyPoseReply {    // py: "<ffffff"
  float x, y, z;          // mm, gövde kayması (z ayakta duruş yüksekliğine göre)
  float roll, pitch, yaw; // derece
};

struct ErrorReply { // py: "<B"
  uint8_t status;   // proto::Status
};

// Jog / yapılandırma onayı: istekle aynı opcode, sonucu taşır.
struct AckReply { // py: "<B"
  uint8_t status; // proto::Status (başarıda OK)
};

#pragma pack(pop)

// Python kopyasının hizalanması için boyutlar tutmalıdır
static_assert(sizeof(SetVelocityMsg) == 12, "SetVelocityMsg size");
static_assert(sizeof(SetBodyPoseMsg) == 24, "SetBodyPoseMsg size");
static_assert(sizeof(SetGaitMsg) == 1, "SetGaitMsg size");
static_assert(sizeof(SetLedMsg) == 8, "SetLedMsg size");
static_assert(sizeof(JogServoMsg) == 3, "JogServoMsg size");
static_assert(sizeof(ProvisionBodyMsg) == 28, "ProvisionBodyMsg size");
static_assert(sizeof(ProvisionMountsMsg) == 96, "ProvisionMountsMsg size");
static_assert(sizeof(ProvisionDirectionMsg) == 72, "ProvisionDirectionMsg size");
static_assert(sizeof(ProvisionTrimMsg) == 72, "ProvisionTrimMsg size");
static_assert(sizeof(ProvisionRangesMsg) == 24, "ProvisionRangesMsg size");
static_assert(sizeof(ProvisionGaitsMsg) == 48, "ProvisionGaitsMsg size");
static_assert(sizeof(ProvisionLimitsMsg) == 32, "ProvisionLimitsMsg size");
static_assert(sizeof(ProvisionBodyPoseMsg) == 48, "ProvisionBodyPoseMsg size");
static_assert(sizeof(ProvisionServoCalMsg) == 108, "ProvisionServoCalMsg size");
static_assert(sizeof(ProvisionPinsMsg) == 18, "ProvisionPinsMsg size");
static_assert(sizeof(TelemetryReply) == 21, "TelemetryReply size");
static_assert(sizeof(VoltageReply) == 4, "VoltageReply size");
static_assert(sizeof(CurrentReply) == 4, "CurrentReply size");
static_assert(sizeof(JointsReply) == 72, "JointsReply size");
static_assert(sizeof(BodyPoseReply) == 24, "BodyPoseReply size");
static_assert(sizeof(ErrorReply) == 1, "ErrorReply size");
static_assert(sizeof(AckReply) == 1, "AckReply size");

// Çerçeveleme (HDLC tarzı kodlayıcı)
//
// Bu dosyanın başında anlatılan çerçeve düzenini uygular.
// encode_frame() eksiksiz bir çerçeveyi çağıranın sağladığı bir tampona
// yazar; FrameParser baytları tek tek alır ve CRC'si geçerli bir çerçeve
// geldiğinde bildirir. CRC bütünlük garantisidir: CRC hatalıysa veya uzunluk
// baytı olanaksızsa ayrıştırıcı bir sonraki SOF'ta sessizce yeniden senkronize olur

// CRC16-CCITT (polinom 0x1021, başlangıç 0xFFFF), bir baytı katar
constexpr uint16_t crc16_update(uint16_t crc, uint8_t byte) {
  crc ^= static_cast<uint16_t>(byte) << 8;
  for (int i = 0; i < 8; ++i)
    crc = (crc & 0x8000) ? static_cast<uint16_t>((crc << 1) ^ 0x1021)
                         : static_cast<uint16_t>(crc << 1);
  return crc;
}

// SOF | LEN | opcode | yük | CRClo | CRChi değerlerini "out" içine yazar (en az
// len + 5 bayt almalıdır). Çerçeve boyutunu, yük çok büyükse 0 döndürür
inline size_t encode_frame(uint8_t opcode, const uint8_t *payload, uint8_t len,
                           uint8_t *out) {
  if (len > cfg::MAX_PAYLOAD)
    return 0;
  uint16_t crc = 0xFFFF;
  size_t n = 0;
  out[n++] = cfg::SOF;
  out[n++] = len;
  crc = crc16_update(crc, len);
  out[n++] = opcode;
  crc = crc16_update(crc, opcode);
  for (uint8_t i = 0; i < len; ++i) {
    out[n++] = payload[i];
    crc = crc16_update(crc, payload[i]);
  }
  out[n++] = static_cast<uint8_t>(crc & 0xFF);        // CRC düşük bayt
  out[n++] = static_cast<uint8_t>((crc >> 8) & 0xFF); // CRC yüksek bayt
  return n;
}

// Bayt bayt alıcı. feed() tam olarak bir kez (geçerli bir çerçeveyi tamamlayan
// baytta) true döndürür; ardından opcode()/payload()/length() bir sonraki
// feed()'e kadar geçerlidir
class FrameParser {
public:
  bool feed(uint8_t b) {
    switch (phase_) {
    case Phase::Sof:
      if (b == cfg::SOF)
        phase_ = Phase::Len;
      return false;
    case Phase::Len:
      if (b > cfg::MAX_PAYLOAD) { // olanaksız uzunluk -> yeniden senkronize ol
        phase_ = (b == cfg::SOF) ? Phase::Len : Phase::Sof;
        return false;
      }
      length_ = b;
      crc_ = crc16_update(0xFFFF, b);
      phase_ = Phase::Opcode;
      return false;
    case Phase::Opcode:
      opcode_ = b;
      crc_ = crc16_update(crc_, b);
      idx_ = 0;
      phase_ = (length_ == 0) ? Phase::CrcLo : Phase::Payload;
      return false;
    case Phase::Payload:
      payload_[idx_++] = b;
      crc_ = crc16_update(crc_, b);
      if (idx_ >= length_)
        phase_ = Phase::CrcLo;
      return false;
    case Phase::CrcLo:
      rx_crc_ = b;
      phase_ = Phase::CrcHi;
      return false;
    case Phase::CrcHi:
      rx_crc_ |= static_cast<uint16_t>(b) << 8;
      phase_ = Phase::Sof;
      return rx_crc_ == crc_; // yalnızca CRC eşleşirse tamamlanır
    }
    return false;
  }

  uint8_t opcode() const { return opcode_; }
  const uint8_t *payload() const { return payload_; }
  uint8_t length() const { return length_; }
  void reset() { phase_ = Phase::Sof; }

private:
  enum class Phase : uint8_t { Sof, Len, Opcode, Payload, CrcLo, CrcHi };
  Phase phase_ = Phase::Sof;
  uint8_t length_ = 0;
  uint8_t opcode_ = 0;
  uint8_t idx_ = 0;
  uint16_t crc_ = 0;    // LEN..yük üzerinden hesaplanan CRC
  uint16_t rx_crc_ = 0; // çerçevede taşınan CRC
  uint8_t payload_[cfg::MAX_PAYLOAD];
};

} // namespace proto
