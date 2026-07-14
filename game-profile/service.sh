#!/system/bin/sh

MODDIR=${0%/*}
CONF="$MODDIR/profile.conf"
PACKAGES="$MODDIR/packages.list"
STATUS="$MODDIR/status"

ENABLE_SCHED_BOOST=1
ENABLE_GPU_MIN_BOOST=1
POLL_SECONDS=3
[ -r "$CONF" ] && . "$CONF"

case "$POLL_SECONDS" in
    ''|*[!0-9]*) POLL_SECONDS=3 ;;
esac
[ "$POLL_SECONDS" -lt 1 ] && POLL_SECONDS=1

while [ "$(getprop sys.boot_completed)" != "1" ]; do
    sleep 5
done

GPU_BASE=/sys/class/kgsl/kgsl-3d0
GPU_MIN="$GPU_BASE/devfreq/min_freq"
GPU_AVAILABLE="$GPU_BASE/devfreq/available_frequencies"
[ -e "$GPU_MIN" ] || GPU_MIN="$GPU_BASE/min_gpuclk"
[ -r "$GPU_AVAILABLE" ] || GPU_AVAILABLE="$GPU_BASE/gpu_available_frequencies"

SCHED_BOOST=
for node in \
    /proc/sys/kernel/sched_boost \
    /sys/devices/system/cpu/cpu_boost/sched_boost \
    /sys/module/cpu_boost/parameters/sched_boost; do
    if [ -e "$node" ]; then
        SCHED_BOOST="$node"
        break
    fi
done

ORIGINAL_GPU_MIN=
GAME_GPU_MIN=
if [ -r "$GPU_MIN" ] && [ -r "$GPU_AVAILABLE" ]; then
    ORIGINAL_GPU_MIN="$(cat "$GPU_MIN" 2>/dev/null)"
    GAME_GPU_MIN="$(tr ' ,' '\n\n' < "$GPU_AVAILABLE" | grep -E '^[0-9]+$' | sort -nu | sed -n '2p')"
    if [ -n "$ORIGINAL_GPU_MIN" ] && [ -n "$GAME_GPU_MIN" ] && \
       [ "$ORIGINAL_GPU_MIN" -gt "$GAME_GPU_MIN" ] 2>/dev/null; then
        GAME_GPU_MIN="$ORIGINAL_GPU_MIN"
    fi
fi

ORIGINAL_SCHED_BOOST=
[ -r "$SCHED_BOOST" ] && ORIGINAL_SCHED_BOOST="$(cat "$SCHED_BOOST" 2>/dev/null)"

write_node() {
    [ -n "$1" ] && [ -w "$1" ] && [ -n "$2" ] && \
        echo "$2" > "$1" 2>/dev/null
}

game_is_running() {
    [ -r "$PACKAGES" ] || return 1
    while IFS= read -r package; do
        case "$package" in
            ''|'#'*) continue ;;
        esac
        pidof "$package" >/dev/null 2>&1 && return 0
    done < "$PACKAGES"
    return 1
}

apply_profile() {
    [ "$ENABLE_SCHED_BOOST" = "1" ] && write_node "$SCHED_BOOST" 1
    [ "$ENABLE_GPU_MIN_BOOST" = "1" ] && write_node "$GPU_MIN" "$GAME_GPU_MIN"
    echo active > "$STATUS"
}

restore_profile() {
    write_node "$SCHED_BOOST" "$ORIGINAL_SCHED_BOOST"
    write_node "$GPU_MIN" "$ORIGINAL_GPU_MIN"
    echo idle > "$STATUS"
}

trap 'restore_profile' EXIT INT TERM
ACTIVE=0
echo idle > "$STATUS"

while true; do
    if game_is_running; then
        if [ "$ACTIVE" -eq 0 ]; then
            apply_profile
            ACTIVE=1
        fi
    elif [ "$ACTIVE" -eq 1 ]; then
        restore_profile
        ACTIVE=0
    fi
    sleep "$POLL_SECONDS"
done
