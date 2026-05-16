
// git show 3b8fbcc6b31765769f411b5b7ec0a54ff2762bb8:audiofp-server/src/main.rs
use audiofp::{AudioBuffer, SampleRate, AfpError};

pub fn load_audio(path: &str) -> Result<(AudioBuffer<'static>, u32), AfpError> {
    use symphonia::core::audio::{AudioBufferRef, Signal};
    use symphonia::core::codecs::DecoderOptions;
    use symphonia::core::errors::Error;
    use symphonia::core::formats::FormatOptions;
    use symphonia::core::io::MediaSourceStream;
    use symphonia::core::meta::MetadataOptions;
    use symphonia::core::probe::Hint;
    use symphonia::default::get_probe;

    let file = std::fs::File::open(path)
        .map_err(|e| AfpError::Io(format!("open: {e}")))?;
    let mss = MediaSourceStream::new(Box::new(file), Default::default());

    let hint = Hint::new();
    let probed = get_probe().format(
        &hint,
        mss,
        &FormatOptions::default(),
        &MetadataOptions::default(),
    ).map_err(|e| AfpError::Io(format!("probe: {e}")))?;

    let mut format = probed.format;
    let track = format.default_track().ok_or_else(|| AfpError::Io("no track".into()))?;

    let mut decoder = symphonia::default::get_codecs()
        .make(&track.codec_params, &DecoderOptions::default())
        .map_err(|e| AfpError::Io(format!("decoder: {e}")))?;

    let mut samples = Vec::<f32>::new();
    let mut sample_rate = 0u32;
    let mut total_frames: u64 = 0;

    loop {
        match format.next_packet() {
            Ok(packet) => {
                let decoded = decoder.decode(&packet)
                    .map_err(|e| AfpError::Io(format!("decode: {e}")))?;

                match decoded {
                    AudioBufferRef::F32(buf) => {
                        sample_rate = buf.spec().rate;
                        let chans = buf.spec().channels.count();

                        total_frames += buf.frames() as u64;

                        for frame in 0..buf.frames() {
                            let mut sum = 0.0;
                            for ch in 0..chans {
                                sum += buf.chan(ch)[frame];
                            }
                            samples.push(sum / chans as f32);
                        }
                    }
                    _ => return Err(AfpError::Io("unsupported sample format".into())),
                }
            }
            Err(Error::ResetRequired) => {
                return Err(AfpError::Io("reset required".into()));
            }
            Err(_) => break,
        }
    }

    if sample_rate == 0 {
        return Err(AfpError::Io("no audio data".into()));
    }

    // Compute duration BEFORE resampling
    let duration_seconds = (total_frames / sample_rate as u64) as u32;

    // Resample to 8 kHz (Wang requirement)
    if sample_rate != 8000 {
        let factor = 8000.0 / sample_rate as f32;
        let new_len = (samples.len() as f32 * factor) as usize;
        let mut resampled = Vec::with_capacity(new_len);

        for i in 0..new_len {
            let src_pos = i as f32 / factor;
            let idx = src_pos.floor() as usize;
            if idx < samples.len() {
                resampled.push(samples[idx]);
            }
        }

        samples = resampled;
    }

    Ok((
        AudioBuffer {
            samples: Box::leak(samples.into_boxed_slice()),
            rate: SampleRate::HZ_8000,
        },
        duration_seconds,
    ))
}
