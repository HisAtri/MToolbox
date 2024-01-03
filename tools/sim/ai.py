import os
import hashlib
import librosa
import numpy as np
from tqdm import tqdm
import concurrent.futures
from sklearn.cluster import KMeans
from scipy.spatial.distance import cosine
from scipy.cluster.hierarchy import linkage, fcluster


# 计算文件的MD5
def calculate_md5(file_path):
    """
    计算文件的 MD5 值

    参数:
        file_path (str): 文件路径

    返回:
        str: 文件的 MD5 值
    """
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


# 提取音频文件的MFCC特征
def feature(path, target_sr=8000, n_mfcc=30, frame_size=16384, hop_length=2048, max_duration=600):
    """
    提取音频文件的 MFCC 特征

    参数:
        path (str): 音频文件路径
        target_sr (int): 目标采样率，默认为8000
        n_mfcc (int): MFCC的数量，默认为50
        frame_size (int): 帧大小，默认为16384
        hop_length (int): 帧之间的跳跃长度，默认为2048
        max_duration (int): 最大持续时间（秒），默认为600秒（10分钟）

    返回:
        numpy.ndarray: MFCC 特征向量
    """
    y, sr = librosa.load(path, sr=target_sr, duration=max_duration)
    y = librosa.effects.preemphasis(y)      # 预加重处理
    y = librosa.util.normalize(y)           # 音量归一化
    mfcc_features = librosa.feature.mfcc(y=y, sr=target_sr, n_mfcc=n_mfcc, n_fft=frame_size, hop_length=hop_length)
    # 转换精度
    # mfcc_features = mfcc_features.astype(np.float32)
    return mfcc_features.flatten()


def cosine_similarity(vector1, vector2):
    """
    计算两个向量之间的余弦相似度

    参数:
        vector1 (numpy.ndarray): 向量1
        vector2 (numpy.ndarray): 向量2

    返回:
        float: 余弦相似度
    """
    similarity = 1 - cosine(vector1, vector2)
    return similarity


# 计算相似度矩阵
def calculate_similarity_matrix(vectors):
    """
    计算向量列表中所有向量之间的余弦相似度矩阵

    参数:
        vectors (list): 向量列表

    返回:
        numpy.ndarray: 相似度矩阵
    """
    max_len = max(len(vector) for vector in vectors)
    padded_vectors = [np.pad(vector, (0, max_len - len(vector))) for vector in vectors]
    similarity_matrix = np.zeros((len(vectors), len(vectors)))
    for i in range(len(vectors)):
        for j in range(i, len(vectors)):
            similarity = cosine_similarity(padded_vectors[i], padded_vectors[j])
            similarity_matrix[i, j] = similarity
            similarity_matrix[j, i] = similarity
    return similarity_matrix


def perform_hierarchical_clustering(pathToMFCC, threshold, fileQuant):
    """
    执行层次聚类并返回聚类结果

    参数:
        pathToMFCC (dict): 特征向量的字典，键为文件路径，值为特征向量
        threshold (float): 相似度阈值
        fileQuant (int): 文件数量

    返回:
        list: 聚类结果
    """
    vectors = list(pathToMFCC.values())     # 将MFCC矩阵装入列表

    # 使用K-Means算法进行预分类
    k = fileQuant // 20                 # 设置簇数
    kmeans = KMeans(n_clusters=k)           # 实例化
    max_len = max(len(vector) for vector in vectors)

    # 统一向量长度，并进行填充
    padded_vectors = []
    for vector in vectors:
        if len(vector) < max_len:
            padded_vector = np.pad(vector, (0, max_len - len(vector)))
        else:
            padded_vector = vector[:max_len]
        padded_vectors.append(padded_vector)

    clusters = kmeans.fit_predict(padded_vectors)   # 获得返回的聚类结果

    print("完成k-means聚类，进行层次聚类")

    clustered_paths = {}                            # 创建空字典
    for i, path in enumerate(pathToMFCC.keys()):    # 遍历pathToMFCC字典的key
        cluster = clusters[i]
        if cluster not in clustered_paths:
            clustered_paths[cluster] = [path]
        else:
            clustered_paths[cluster].append(path)

    final_clusters = []
    for cluster_paths in clustered_paths.values():
        cluster_vectors = [pathToMFCC[path] for path in cluster_paths]
        similarity_matrix = calculate_similarity_matrix(cluster_vectors)

        # 使用层次聚类进行细分
        if len(cluster_paths) > 1:
            linkage_matrix = linkage(similarity_matrix, method="centroid")
            clusters = fcluster(linkage_matrix, threshold, criterion="distance")

            sub_clusters = {}
            for i, path in enumerate(cluster_paths):
                sub_cluster = clusters[i]
                if sub_cluster not in sub_clusters:
                    sub_clusters[sub_cluster] = [path]
                else:
                    sub_clusters[sub_cluster].append(path)

            # 将细分的结果合并
            merged_sub_clusters = []
            for sub_cluster_paths in sub_clusters.values():
                if len(sub_cluster_paths) > 1:
                    merged_sub_clusters.append(sub_cluster_paths)
                else:
                    merged_sub_clusters.append([sub_cluster_paths[0]])

            final_clusters.extend(merged_sub_clusters)
        else:
            final_clusters.append(cluster_paths)  # 单个样本的簇直接添加到最终结果中

    return final_clusters


def process_file(args):
    file_path = args
    # print(file_path)
    file_md5 = calculate_md5(file_path)
    global md5ToMFCC, pathToMFCC, fileQuant, fatalError

    # 如果MD5存在，直接赋值
    if file_md5 in md5ToMFCC:
        mfcc_features = md5ToMFCC[file_md5]
    # 如果MD5不存在，则Feature
    else:
        try:
            # 计算
            mfcc_features = feature(file_path)
            # 赋值
            md5ToMFCC[file_md5] = mfcc_features
        except:
            print("Error:" + file_path)
            fatalError.append(file_md5)
            fileQuant += 1
            return

    # 处理多声道的MFCC特征向量
    # 如果声道数大于1，则平均混合
    if len(mfcc_features.shape) > 1:
        mfcc_features = np.mean(mfcc_features, axis=1)  # 平均混合多个声道

    pathToMFCC[file_path] = mfcc_features
    fileQuant += 1  # 对文件数进行计数


def process_audio_folder(folder_path, threads):
    """
    处理音频文件夹并提取 MFCC 特征

    参数:
        folder_path (str): 音频文件夹路径

    返回:
       Dict[str, numpy.ndarray]: 文件路径到 MFCC 特征向量的映射
    """
    global md5ToMFCC, pathToMFCC, fileQuant, fatalError
    md5ToMFCC = {}
    pathToMFCC = {}
    fileQuant = 0
    fatalError = []

    if os.path.exists("MFCC.npy"):
        md5ToMFCC = np.load("MFCC.npy", allow_pickle=True).item()

    file_paths = []
    for root, _, files in os.walk(folder_path):
        for filename in files:
            if filename.lower().endswith(('.wav', '.mp3', '.flac', '.ogg', '.aac', '.m4a')):
                file_path = os.path.join(root, filename)
                file_paths.append(file_path)

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        results = list(tqdm(executor.map(process_file, file_paths), total=len(file_paths), desc="MFCC.Progress"))

    np.save("MFCC.npy", md5ToMFCC)

    print("完成特征向量提取，正在进行聚类...")
    return pathToMFCC, fileQuant, fatalError


# 主程序
def main(folder_path, threshold=0.12, threads=8, debug=False):
    pathToMFCC, fileQuant, fatalError = process_audio_folder(folder_path, threads)       # 完成MFCC
    clusters = perform_hierarchical_clustering(pathToMFCC, threshold, fileQuant)    # 进行聚类
    # 输出结果
    duplicateList = []
    for i, cluster in enumerate(clusters):
        if debug or (len(cluster) > 1):
            duplicateList.append(cluster)
    return duplicateList, fatalError


if __name__ == "__main__":
    folder_path = "F:\\programs\\MuSIM\\test"  # 音频文件夹路径
    threads = 8         # 线程数
    threshold = 0.125   # 聚类阈值（推荐在0.1~0.2之间）
    debug = False       # debug模式；True：输出全部聚类结果；False：仅输出聚类集合元素大于1的结果
    main(folder_path, threshold, threads, debug)
