import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.io import wavfile

def mix_channels(data):
    # 将多个声道混合成一个单声道
    return np.mean(data, axis=-1)

def generate_spectrogram(audio_file, window_size=1024, hop_size=512, fs=44100):
    # 读取音频文件
    rate, data = wavfile.read(audio_file)

    # 将多个声道混合成一个单声道
    if len(data.shape) > 1:
        data = mix_channels(data)

    # 使用窗口函数进行快速傅里叶变换
    window = np.hanning(window_size)
    num_frames = int((len(data) - window_size) / hop_size) + 1

    spectrogram = np.zeros((window_size // 2, num_frames))

    for t in range(num_frames):
        start = t * hop_size
        end = start + window_size
        frame = data[start:end] * window

        spectrum = np.fft.fft(frame)
        magnitude = np.abs(spectrum[:window_size // 2])
        spectrogram[:, t] = magnitude

    # 将幅度转换为分贝
    spectrogram = 10 * np.log10(spectrogram + 1e-9)

    return spectrogram, rate

def plot_spectrogram(spectrogram, rate, colormap='viridis'):
    colors = [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0), (1, 1, 0), (1, 0, 0)]  # 你可以定义自己的颜色
    cmap = LinearSegmentedColormap.from_list(colormap, colors, N=256)
    plt.imshow(spectrogram, aspect='auto', origin='lower', cmap=cmap, extent=[0, len(spectrogram[0]), 20, rate // 2])
    plt.colorbar(label='Magnitude (dB)')
    plt.xlabel('Time (frames)')
    plt.ylabel('Frequency (Hz)')
    plt.title('Spectrogram')
    plt.show()

# 音频文件路径
audio_file = (r'H:\sp\y.wav')
spectrogram, rate = generate_spectrogram(audio_file)
plot_spectrogram(spectrogram, rate)