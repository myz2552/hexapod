#pragma once
//
// Bacak başına ileri/ters kinematik.
//
// Çerçeveler:
//   - inverse()'e verilen ayak hedefleri DÜNYA (zemin) çerçevesindedir.
//   - body_pos/body_rpy gövdenin o dünya çerçevesindeki pozudur; burada
//     hesaba katılır, böylece gövde eğilirken ayak hedefi zeminde yerinde
//     kalır.
//   - Her bacağın montaj çerçevesi, gövde çerçevesinde bir yaw dönmesi + ötelemedir.
//
// Açılar kinematik çerçevede radyandır. Servo uzayına eşleme
// (yön/trim/kırpma ve dereceye dönüşüm) burada değil, robot
// katmanında yapılır.

#include <cmath>

#include "core/config.hpp"
#include "utils/math.hpp"

namespace kin {

using math::Vec3;

struct IkResult {
  bool ok = false;
  float coxa = 0.0f;  // rad
  float femur = 0.0f; // rad
  float tibia = 0.0f; // rad
};

// Gövde çerçevesinde bacak montaj pozu, derlenmiş config'ten
inline Vec3 mount_pos(int leg) {
  return {cfg::MOUNT[leg].x, cfg::MOUNT[leg].y, cfg::MOUNT[leg].z};
}
inline float mount_yaw(int leg) {
  return math::deg2rad(cfg::MOUNT[leg].yaw_deg);
}

// Bacak çerçevesinde 2 uzuvlu düzlemsel IK: coxa +z etrafında bir yaw'dır; femur ve
// tibia, radyal düzleme paralel ama COXA_OFFSET kadar yana kaydırılmış dikey bir
// düzlemde durur. Bu yüzden coxa, ofsetin gördüğü açı kadar hedefin yönünü aşarak
// dönmelidir. Hedef erişim dışındaysa ok=false döndürür; eksene ofsetin kendisinden
// daha yakın hedefler de buna dahildir
inline IkResult leg_inverse(float x, float y, float z) {
  IkResult r;
  const float rho2 = x * x + y * y;
  if (rho2 < cfg::COXA_OFFSET * cfg::COXA_OFFSET) return r; // ofsetin içinde
  // Bacak düzlemi içinde kat edilen mesafe ve ofsetin kapladığı açı
  const float radial = std::sqrt(rho2 - cfg::COXA_OFFSET * cfg::COXA_OFFSET);
  const float coxa = std::atan2(y, x) - std::atan2(cfg::COXA_OFFSET, radial);
  const float reach = radial - cfg::COXA_LEN;
  const float d = std::sqrt(reach * reach + z * z);
  if (d > (cfg::FEMUR_LEN + cfg::TIBIA_LEN) ||
      d < std::fabs(cfg::FEMUR_LEN - cfg::TIBIA_LEN))
    return r; // erişilemez

  const float cos_tibia = (cfg::FEMUR_LEN * cfg::FEMUR_LEN +
                           cfg::TIBIA_LEN * cfg::TIBIA_LEN - d * d) /
                          (2.0f * cfg::FEMUR_LEN * cfg::TIBIA_LEN);

  const float tibia =
      std::acos(math::clampf(cos_tibia, -1.0f, 1.0f)) - math::PI;

  const float cos_femur = (cfg::FEMUR_LEN * cfg::FEMUR_LEN + d * d -
                           cfg::TIBIA_LEN * cfg::TIBIA_LEN) /
                          (2.0f * cfg::FEMUR_LEN * d);

  const float femur =
      std::atan2(z, reach) + std::acos(math::clampf(cos_femur, -1.0f, 1.0f));

  r.ok = true;
  r.coxa = coxa;
  r.femur = femur;
  r.tibia = tibia;
  return r;
}

// Bacak çerçevesinde FK: eklem açıları (rad) -> ayak konumu (mm)
inline Vec3 leg_forward(float coxa, float femur, float tibia) {
  const float radial = cfg::COXA_LEN + cfg::FEMUR_LEN * std::cos(femur) +
                       cfg::TIBIA_LEN * std::cos(femur + tibia);
  const float z = cfg::FEMUR_LEN * std::sin(femur) +
                  cfg::TIBIA_LEN * std::sin(femur + tibia);
  // Bacak, coxa'nın etrafında döndürdüğü kendi düzlemi içinde uzanır
  const float c = std::cos(coxa), s = std::sin(coxa);
  return {radial * c - cfg::COXA_OFFSET * s, radial * s + cfg::COXA_OFFSET * c,
          z};
}

// Tek bacak için tam IK: dünya çerçevesinde ayak hedefi + gövde pozu -> eklem açıları
inline IkResult inverse(int leg, const Vec3 &foot_world, const Vec3 &body_pos,
                        const Vec3 &body_rpy) {
  const Vec3 in_body = math::world_to_body(foot_world, body_pos, body_rpy);
  const Vec3 in_leg = math::rot_z(-mount_yaw(leg), in_body - mount_pos(leg));
  return leg_inverse(in_leg.x, in_leg.y, in_leg.z);
}

// Tek bacak için tam FK. apply_body=false ile GÖVDE çerçevesindeki ayak konumunu
// döndürür (ölçülen eklem açılarından bacak durumunu başlatmak için kullanılır;
// gövde argümanı verilmeden çağrılan Python forward() ile tamamen aynı)
inline Vec3 forward(int leg, float coxa, float femur, float tibia,
                    const Vec3 &body_pos, const Vec3 &body_rpy,
                    bool apply_body) {
  const Vec3 in_body =
      math::rot_z(mount_yaw(leg), leg_forward(coxa, femur, tibia)) +
      mount_pos(leg);
  return apply_body ? math::body_to_world(in_body, body_pos, body_rpy)
                    : in_body;
}

} // namespace kin
