// Host testi: hat protokolü, C++'tan C++'a (encode_frame -> FrameParser).
//
// Kodlayıcının gidiş-dönüşte bozulmadığını, tipli yük struct'larının iki uçta da
// memcpy yaklaşımıyla korunduğunu, CRC'nin bozulmayı reddettiğini ve ayrıştırıcının
// çöp verinin ardından yeniden senkronize olduğunu gösterir.

#include <cstdio>
#include <cstring>

#include "check.hpp"
#include "communication/protocol.hpp"

using namespace proto;

// Bir tamponu ayrıştırıcıdan geçirir. Çerçeveyi tamamlayan baytın 1 tabanlı indisini,
// hiçbiri tamamlamadıysa 0 döndürür.
static int feed_all(FrameParser& p, const uint8_t* buf, size_t n) {
    for (size_t i = 0; i < n; ++i)
        if (p.feed(buf[i])) return int(i) + 1;
    return 0;
}

static void framing_roundtrip() {
    std::printf("frame encode -> parse round-trip\n");
    // Yük bilerek SOF (0xAA) ve 0x55'e eşit baytlar içerir; LEN'e dayalı çerçevelemenin
    // bunlara takılmadığını gösterir.
    const uint8_t payload[] = {1, 2, 3, 0xAB, 0xCD, 0x55, 0xAA};
    uint8_t frame[64];
    size_t n = encode_frame(uint8_t(Opcode::GetTelemetry), payload, sizeof(payload), frame);
    CHECK(n == sizeof(payload) + 5, "frame size = payload + 5");

    FrameParser p;
    int done = feed_all(p, frame, n);
    CHECK(done == int(n), "parser completes on the final byte");
    CHECK(p.opcode() == uint8_t(Opcode::GetTelemetry), "opcode round-trips");
    CHECK(p.length() == sizeof(payload), "length round-trips");
    CHECK(std::memcmp(p.payload(), payload, sizeof(payload)) == 0, "payload round-trips");
}

static void zero_length_frame() {
    std::printf("zero-length payload (e.g. Enable)\n");
    uint8_t frame[8];
    size_t n = encode_frame(uint8_t(Opcode::Enable), nullptr, 0, frame);
    CHECK(n == 5, "empty frame is 5 bytes");
    FrameParser p;
    int done = feed_all(p, frame, n);
    CHECK(done == int(n), "empty frame parses");
    CHECK(p.opcode() == uint8_t(Opcode::Enable), "opcode round-trips");
    CHECK(p.length() == 0, "length is zero");
}

static void typed_payload_roundtrip() {
    std::printf("typed payload memcpy round-trip (SetVelocity)\n");
    SetVelocityMsg sent{123.5f, -45.25f, 12.0f};
    uint8_t frame[32];
    size_t n = encode_frame(uint8_t(Opcode::SetVelocity),
                            reinterpret_cast<const uint8_t*>(&sent), sizeof(sent), frame);
    FrameParser p;
    feed_all(p, frame, n);
    SetVelocityMsg recv;
    std::memcpy(&recv, p.payload(), sizeof(recv));
    CHECK(recv.vx == sent.vx && recv.vy == sent.vy && recv.wz == sent.wz,
          "float fields survive encode/parse/memcpy");
}

static void crc_rejects_corruption() {
    std::printf("CRC rejects a corrupted frame\n");
    const uint8_t payload[] = {10, 20, 30, 40};
    uint8_t frame[16];
    size_t n = encode_frame(uint8_t(Opcode::GetJoints), payload, sizeof(payload), frame);
    frame[3] ^= 0xFF;  // yükün ilk baytını ters çevir
    FrameParser p;
    int done = feed_all(p, frame, n);
    CHECK(done == 0, "no frame completes when a byte is corrupted");
}

static void resync_after_garbage() {
    std::printf("parser resyncs after leading garbage\n");
    const uint8_t payload[] = {7, 8, 9};
    uint8_t frame[16];
    size_t n = encode_frame(uint8_t(Opcode::SetGait), payload, sizeof(payload), frame);

    uint8_t stream[32];
    size_t k = 0;
    stream[k++] = 0x00; stream[k++] = 0xAA; stream[k++] = 0xFF;  // başıboş bir SOF dahil gürültü
    std::memcpy(stream + k, frame, n); k += n;

    FrameParser p;
    int done = feed_all(p, stream, k);
    CHECK(done != 0, "valid frame found after garbage");
    CHECK(p.opcode() == uint8_t(Opcode::SetGait), "opcode correct after resync");
    CHECK(std::memcmp(p.payload(), payload, sizeof(payload)) == 0, "payload correct after resync");
}

static void kinds() {
    std::printf("message kinds\n");
    CHECK(kind_of(Opcode::SetVelocity)  == Kind::FireAndForget, "SetVelocity is fire-and-forget");
    CHECK(kind_of(Opcode::Heartbeat)    == Kind::FireAndForget, "Heartbeat is fire-and-forget");
    CHECK(kind_of(Opcode::GetVoltage)   == Kind::RequestReply,  "GetVoltage is request/reply");
    CHECK(kind_of(Opcode::GetTelemetry) == Kind::RequestReply,  "GetTelemetry is request/reply");
}

int main() {
    framing_roundtrip();
    zero_length_frame();
    typed_payload_roundtrip();
    crc_rejects_corruption();
    resync_after_garbage();
    kinds();
    return test_summary("protocol");
}
