#pragma once
//
// Küçük host test yardımcısı: bir CHECK makrosu, float karşılaştırması ve özet.
// Her test_*.cpp kendi başına bir çalıştırılabilir dosyadır, bu yüzden g_failures her ikili dosyaya özeldir.

#include <cstdio>
#include <cmath>

inline int g_failures = 0;

#define CHECK(cond, msg) do {                                          \
    if (cond) std::printf("  ok    %s\n", (msg));                      \
    else { std::printf("  FAIL  %s   [%s:%d]\n", (msg), __FILE__, __LINE__); ++g_failures; } \
} while (0)

inline bool approx(float a, float b, float eps) { return std::fabs(a - b) <= eps; }

inline int test_summary(const char* name) {
    std::printf("\n[%s] %s - %d failure(s)\n",
                name, g_failures ? "FAILED" : "PASSED", g_failures);
    return g_failures ? 1 : 0;
}
