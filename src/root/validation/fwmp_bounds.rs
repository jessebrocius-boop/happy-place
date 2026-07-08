// src/root/validation/fwmp_bounds.rs

/// The temporal and computational limits for the FWMP Epoch.
pub struct EpochConstraints {
    pub duration_cycles: u64,
    pub max_handshake_cycles: u64, // Must be << duration_cycles
    pub nonce_entropy_threshold: u64,
}

/// Baked into the read-only data segment (.rodata) at compile time.
pub const FWMP_BOUNDS: EpochConstraints = EpochConstraints {
    duration_cycles: 1_024_000,
    max_handshake_cycles: 5_120, // 0.5% limit for Gate 1 verification - The Red Line
    nonce_entropy_threshold: 4096, // Min noise floor samples required
};
