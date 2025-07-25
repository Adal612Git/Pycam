export class ToleranceWindow {
    private start: number | null = null;
    constructor(private readonly durationMs = 5000) {}

    reset() {
        this.start = null;
    }

    update(isBad: boolean): boolean {
        const now = Date.now();
        if (isBad) {
            if (this.start === null) this.start = now;
            return now - this.start >= this.durationMs;
        } else {
            this.reset();
            return false;
        }
    }
}
