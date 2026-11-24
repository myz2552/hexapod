#pragma once
//
// Firmware'in robot hakkında bilmesi gereken her şey:
// uzuv uzunlukları, her bacağın montaj yeri, servo-kinematik eşleme,
// yürüyüş parametreleri, kart pinleri ve güvenlik sınırları.
//
// SDK'dan bağımsız: saf çekirdek ve testler Pico SDK olmadan dahil edebilsin
// diye yalnızca int/float/enum içerir. UART ile ilgili şeyler platforma
// bağlıdır ve platform koduyla birlikte durur; burada yalnızca pin numaraları
// vardır.
//
// Birimler: uzunluk mm, açı derece. Standart bacak sırası Leg enum'u ile
// sabitlenmiştir ve Pi'nin varsaydığı sırayla aynı olmalıdır.
//
// Derlenmiş varsayılanlar ve yapılandırmayla gelen değerler
// --------------------------------------------------------
// Aşağıdaki değerler derlenmiş VARSAYILANLARDIR: kart tam olarak bunlarla tek
// başına çalışır. Pi'nin bağlanırken değiştirmesine izin verilen her şey (geometri,
// kinematik eşleme, yürüyüşler, güvenlik sınırları) burada `constexpr` yerine
// değiştirilebilir bir `inline` global'dir; böylece yapılandırma doğrudan ona atama
// yapar ve mevcut tüm okuma noktaları değişmeden çalışmaya devam eder. Asla
// yapılandırılamayan yapısal bilgiler (bacak/eklem sayıları, servo_channel
// formülü, kart GPIO'ları, kontrol frekansı, taşıma sabitleri) `constexpr` kalır.
//
// Servo başına fiziksel kalibrasyon (darbe genişlikleri) ve mantıksal->fiziksel pin
// eşlemesi burada DEĞİLDİR: bunlar HAL'in (hw::Interface) işidir ve doğrudan
// sürücüye gönderilir, çünkü saf çekirdeğin üzerinde çalıştığı kinematik modeli
// değil, kablolamayı ve tek tek servoları tanımlarlar.

#include <cstdint>

namespace cfg {

// Kullanışlı sabitler (yapısal, asla yapılandırılmaz)
constexpr int N_LEGS = 6;
constexpr int N_JOINTS = 3;
constexpr int N_SERVOS = N_LEGS * N_JOINTS;

enum Leg : uint8_t {
  FRONT_RIGHT = 0,
  MIDDLE_RIGHT,
  REAR_RIGHT,
  REAR_LEFT,
  MIDDLE_LEFT,
  FRONT_LEFT,
};

enum Joint : uint8_t { COXA = 0, FEMUR, TIBIA };

// Bacak uzuv geometrisi (mm), altı bacak için ortak. COXA_LEN, coxa ekseninden
// coxa-femur eklemine kadar olan RADYAL mesafedir; COXA_OFFSET bu eklemin coxa
// ekseninin ne kadar yanında durduğudur (+ sol, bacak boyunca dışarı bakarken);
// femur/tibia düzlemini eksenden geçirmek yerine yana kaydırır.
inline float COXA_LEN = 68.0f;
inline float COXA_OFFSET = 0.0f;
inline float FEMUR_LEN = 76.7f;
inline float TIBIA_LEN = 99.6f;

// Her bacağın gövdeye montaj yeri (gövde çerçevesi)
struct LegMount {
  float x;       // mm
  float y;       // mm
  float z;       // mm, coxa-femur ekleminin gövde orijinine göre yüksekliği
  float yaw_deg; // coxa ekseninin montaj yaw açısı
};
inline LegMount MOUNT[N_LEGS] = {
    // x, y, z, yaw
    {82.0f, -57.0f, 0.0f, -45.0f},   // FRONT_RIGHT
    {0.0f, -71.0f, 0.0f, -90.0f},    // MIDDLE_RIGHT
    {-82.0f, -57.0f, 0.0f, -135.0f}, // REAR_RIGHT
    {-82.0f, 57.0f, 0.0f, 135.0f},   // REAR_LEFT
    {0.0f, 71.0f, 0.0f, 90.0f},      // MIDDLE_LEFT
    {82.0f, 57.0f, 0.0f, 45.0f},     // FRONT_LEFT
};

// Servo-kinematik eşleme
// IK temiz bir kinematik çerçevede çalışır; servolar ona birebir uymak zorunda değildir:
//
//      doğrudan: servo_deg = clamp(kin_deg * direction + trim_deg, min_deg, max_deg)
//      ters    : kin_deg    = (servo_deg - trim_deg) / direction
//
// DIRECTION ve TRIM_DEG SERVO BAŞINADIR (bacak öncelikli, cfg::servo_channel sırası);
// böylece config YAML'ındaki hardware.direction / hardware.trim ile birebir eşleşir
// ve farklı monte edilmiş bir bacak yalnızca kendi değerlerini değiştirebilir. Bu
// robotta değerler tüm bacaklarda aynıdır (bir montaj kuralı), ama servo başına
// tutmak eski düzenle uyumludur ve bacak başına ayara imkân bırakır.
inline float DIRECTION[N_SERVOS] = {
    // coxa, femur, tibia
    -1.0f, 1.0f, -1.0f, // FRONT_RIGHT
    -1.0f, 1.0f, -1.0f, // MIDDLE_RIGHT
    -1.0f, 1.0f, -1.0f, // REAR_RIGHT
    -1.0f, 1.0f, -1.0f, // REAR_LEFT
    -1.0f, 1.0f, -1.0f, // MIDDLE_LEFT
    -1.0f, 1.0f, -1.0f, // FRONT_LEFT
};
inline float TRIM_DEG[N_SERVOS] = {
    // coxa, femur, tibia
    0.0f, 0.0f, -163.0f, // FRONT_RIGHT
    0.0f, 0.0f, -163.0f, // MIDDLE_RIGHT
    0.0f, 0.0f, -163.0f, // REAR_RIGHT
    0.0f, 0.0f, -163.0f, // REAR_LEFT
    0.0f, 0.0f, -163.0f, // MIDDLE_LEFT
    0.0f, 0.0f, -163.0f, // FRONT_LEFT
};

// Servo uzayında kırpma, EKLEM TİPİ başına (tüm coxa'lar aynı aralığı paylaşır vb.).
// Config YAML'ındaki safety.{coxa,femur,tibia}_range ile aynıdır.
struct JointRange {
  float min_deg;
  float max_deg;
};
inline JointRange RANGE[N_JOINTS] = {
    {-90.0f, 90.0f},  // COXA
    {-90.0f, 90.0f},  // FEMUR
    {-120.0f, 0.0f},  // TIBIA
};

// (bacak, eklem) çiftini süren servo kanalı: bacak öncelikli, 0..17. Pi ve
// simülasyon/URDF ile paylaşılan standart MANTIKSAL sıra; her kanalın arkasındaki
// fiziksel pin HAL'in işidir (ayrıca yapılandırılır).
constexpr uint8_t servo_channel(int leg, int joint) {
  return static_cast<uint8_t>(leg * N_JOINTS + joint);
}

// Yürüyüş parametreleri
struct GaitParams {
  float duty_factor; // döngü boyunca bacağın destek fazında geçirdiği oran
  float step_height; // mm, salınımda en yüksek kaldırma
  float max_stride;  // mm, adım hızla birlikte buraya kadar büyür, sonra hareket ölçeklenir
                     // sınırlar
  float overlap;     // gruplar arası faz örtüşmesi (0 = yok)
};
inline GaitParams GAIT[3] = {
    // duty, step_h, max_stride, overlap
    {0.5500f, 30.0f, 90.0f, 0.0f},  // TRIPOD
    {0.8333f, 30.0f, 90.0f, 0.0f},  // WAVE
    {0.6700f, 30.0f, 110.0f, 0.0f}, // RIPPLE
};

// Sabit tempolu hareket modeli: her hızda CYCLE_TIME saniyede bir tam yürüyüş
// döngüsü; adım uzunluğu komut verilen hızla ölçeklenir
inline float CYCLE_TIME = 0.8f;       // s  (1.25 Hz tempo)
inline float STANCE_RADIUS = 155.0f;  // mm (nötr ayak noktasının montaj noktasına uzaklığı)
inline float STANDING_HEIGHT = 80.0f; // mm (ayakta dururken gövde yüksekliği)

// Komut sınırları ve yumuşatma
inline float LIN_VEL_MAX = 300.0f;   // mm/s
inline float ANG_VEL_MAX = 60.0f;    // derece/s
inline float VEL_SMOOTH_TAU = 0.05f; // s, birinci dereceden hız yumuşatma

// Gövde pozu ara değer hızları
inline float BODY_LIN_VEL_MAX = 50.0f; // mm/s
inline float BODY_ANG_VEL_MAX = 30.0f; // derece/s
inline float JOINT_VEL_MAX = 200.0f;   // derece/s

// Gövde pozu komut sınırları; simetrik olmak zorunda olmasınlar diye her biri bağımsız
// bir [min, max]. x/y/z mm (z, STANDING_HEIGHT'a göre); roll/pitch/yaw derece.
struct BodyPoseLimits {
  float x_min, x_max;
  float y_min, y_max;
  float z_min, z_max;
  float roll_min, roll_max;
  float pitch_min, pitch_max;
  float yaw_min, yaw_max;
};
inline BodyPoseLimits BODY_POSE = {
    -50.0f, 50.0f,   // x
    -50.0f, 50.0f,   // y
    -20.0f, 20.0f,   // z
    -10.0f, 10.0f,   // roll
    -10.0f, 10.0f,   // pitch
    -10.0f, 10.0f,   // yaw
};

// Servo2040 pinleri (yapısal)
// 18 servo kanalı, 6 WS2812 LED, analog çoklayıcı ve ortak ADC'nin hepsi
// Pimoroni servo2040 namespace'inden gelir. Bunlar GPIO'lardır
constexpr unsigned UART_TX_PIN = 20;
constexpr unsigned UART_RX_PIN = 21;
constexpr unsigned POWER_CUTOFF_PIN = 19; // güç kesme hattı
// NOT: kartın mevcut sürümünde donanımsal aşırı akım kesmesi çalışmıyor, bu yüzden
// kontrol döngüsü CURRENT_MAX'ı (ve VOLTAGE_MIN düşük voltaj kesmesini)
// yazılımla uygular

// Kontrol döngüsü (yapısal)
constexpr float CONTROL_RATE_HZ = 50.0f;
constexpr unsigned WATCHDOG_TIMEOUT_MS = 500; // bu süre içinde hedef değer/heartbeat gelmezse -> otomatik otur ve gücü kes

// Güvenlik (yapılandırılabilir: Pi yazılım kesmelerini sıkılaştırabilir/gevşetebilir).
// İkisi de kontrol döngüsünde, ama yalnızca enerji varken uygulanır.
inline float CURRENT_MAX = 12.0f;  // A, yazılımla aşırı akım kesmesi -> FAULT
inline float VOLTAGE_MIN = 5.0f;   // V, yazılımla düşük voltaj kesmesi  -> FAULT

// Taşıma sabitleri (yapısal)
constexpr uint32_t BAUD = 921600;
constexpr uint8_t SOF = 0xAA;
constexpr uint8_t MAX_PAYLOAD = 128; // en büyüğü GetJoints yanıtı (72 B)

} // namespace cfg
