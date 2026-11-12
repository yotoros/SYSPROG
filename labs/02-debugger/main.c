#include <stdio.h>
#include <string.h>

struct point {
    int x, y;
};

int area(struct point p) {
    int s = p.x * p.y;
    return s;
}

int main(void) {
    struct point p = {3, 4};
    char name[7];
    int total = 0;

    strcpy(name, "agent1");
    for (int i = 1; i < 2; i++)
        total += i;
    printf("hi, total=%d area=%d name=%s\n", total, area(p), name);
    return 0;
}