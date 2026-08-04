#!/usr/bin/env python3
"""
硬件检测与性能调度模块 v3.0
自动检测用户电脑硬件配置，动态调整资源分配
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置文件路径
HARDWARE_CACHE_PATH = Path.home() / '.contract-review' / 'hardware.json'
CACHE_TTL_SECONDS = 3600  # 缓存1小时


class HardwareDetector:
    """硬件检测器 - 自动检测 CPU / 内存 / GPU"""
    
    def __init__(self):
        self._cached_info: Optional[Dict[str, Any]] = None
    
    def detect(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        检测硬件信息（带缓存）
        
        Returns:
            {
                'cpu_cores': int,        # CPU 核心数
                'cpu_freq_mhz': float,   # CPU 频率（MHz）
                'memory_total_gb': float,# 总内存（GB）
                'memory_available_gb': float,  # 可用内存（GB）
                'has_gpu': bool,         # 是否有独立 GPU
                'gpu_name': str,         # GPU 型号
                'gpu_memory_gb': float,  # 显存（GB）
                'detected_at': float,    # 检测时间戳
            }
        """
        # 尝试读取缓存
        if not force_refresh and self._cached_info is None:
            self._cached_info = self._read_cache()
        
        if not force_refresh and self._cached_info is not None:
            cache_age = time.time() - self._cached_info.get('detected_at', 0)
            if cache_age < CACHE_TTL_SECONDS:
                return self._cached_info
        
        # 实时检测
        info = self._do_detect()
        
        # 写入缓存
        self._cached_info = info
        self._write_cache(info)
        
        return info
    
    def get_optimal_config(self, hardware_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        根据硬件信息生成最优配置
        
        Returns:
            {
                'ocr_batch_size': int,       # OCR 并行页数
                'ocr_use_gpu': bool,         # OCR 是否使用 GPU
                'llm_timeout': int,          # LLM 超时时间（秒）
                'max_concurrent_reviews': int,  # 最大并发审查数
                'text_chunk_size': int,      # 文本分块大小
                'hardware_tier': str,        # 硬件等级：low / medium / high
            }
        """
        if hardware_info is None:
            hardware_info = self.detect()
        
        cpu_cores = hardware_info.get('cpu_cores', 4)
        memory_total = hardware_info.get('memory_total_gb', 8)
        memory_available = hardware_info.get('memory_available_gb', 4)
        
        # 计算硬件等级（取 CPU 和内存的较低者）
        cpu_tier = 'high' if cpu_cores >= 8 else ('medium' if cpu_cores >= 4 else 'low')
        mem_tier = 'high' if memory_total >= 16 else ('medium' if memory_total >= 8 else 'low')
        
        # 取较低等级
        tier = min([cpu_tier, mem_tier], key=lambda t: {'low': 0, 'medium': 1, 'high': 2}[t])
        
        # PaddleOCR GPU 模式检测
        has_gpu = hardware_info.get('has_gpu', False)
        gpu_memory = hardware_info.get('gpu_memory_gb', 0)
        ocr_use_gpu = has_gpu and gpu_memory >= 2.0  # 需要至少 2GB 显存
        
        if tier == 'low':
            config = {
                'ocr_batch_size': 1,
                'ocr_use_gpu': False,
                'llm_timeout': 300,
                'max_concurrent_reviews': 1,
                'text_chunk_size': 8000,
                'hardware_tier': 'low',
            }
        elif tier == 'medium':
            config = {
                'ocr_batch_size': 4,
                'ocr_use_gpu': ocr_use_gpu,
                'llm_timeout': 180,
                'max_concurrent_reviews': 2,
                'text_chunk_size': 15000,
                'hardware_tier': 'medium',
            }
        else:  # high
            config = {
                'ocr_batch_size': 8,
                'ocr_use_gpu': ocr_use_gpu,
                'llm_timeout': 120,
                'max_concurrent_reviews': 4,
                'text_chunk_size': 20000,
                'hardware_tier': 'high',
            }
        
        # 根据可用内存微调
        if memory_available < 2.0:
            config['ocr_batch_size'] = 1
            config['max_concurrent_reviews'] = 1
            config['hardware_tier'] += '_memory_constrained'
        
        return config
    
    def format_hardware_summary(self, hardware_info: Optional[Dict[str, Any]] = None) -> str:
        """生成硬件摘要字符串"""
        if hardware_info is None:
            hardware_info = self.detect()
        
        cpu = hardware_info.get('cpu_cores', '?')
        mem_total = hardware_info.get('memory_total_gb', 0)
        mem_avail = hardware_info.get('memory_available_gb', 0)
        gpu = hardware_info.get('gpu_name', '无独立GPU')
        
        return f"CPU {cpu}核 | 内存 {mem_total:.1f}GB (可用 {mem_avail:.1f}GB) | GPU: {gpu}"
    
    def _do_detect(self) -> Dict[str, Any]:
        """执行硬件检测"""
        info = {
            'cpu_cores': 4,
            'cpu_freq_mhz': 2500.0,
            'memory_total_gb': 8.0,
            'memory_available_gb': 4.0,
            'has_gpu': False,
            'gpu_name': '集成显卡',
            'gpu_memory_gb': 0.0,
            'detected_at': time.time(),
        }
        
        # CPU 和内存检测（优先使用 psutil，回退到平台命令）
        try:
            import psutil
            info['cpu_cores'] = psutil.cpu_count(logical=True) or 4
            info['cpu_freq_mhz'] = psutil.cpu_freq().current if psutil.cpu_freq() else 2500.0
            vm = psutil.virtual_memory()
            info['memory_total_gb'] = vm.total / (1024 ** 3)
            info['memory_available_gb'] = vm.available / (1024 ** 3)
        except ImportError:
            # psutil 不可用，使用平台特定命令
            self._detect_without_psutil(info)
        
        # GPU 检测
        self._detect_gpu(info)
        
        return info
    
    def _detect_without_psutil(self, info: Dict[str, Any]):
        """无 psutil 时的回退检测方案"""
        import subprocess
        import platform
        
        system = platform.system()
        
        try:
            if system == 'Windows':
                # Windows: wmic 命令
                result = subprocess.run(
                    ['wmic', 'cpu', 'get', 'NumberOfCores'],
                    capture_output=True, text=True, timeout=10
                )
                lines = [l.strip() for l in result.stdout.strip().split('\n') if l.strip().isdigit()]
                if lines:
                    info['cpu_cores'] = int(lines[0])
                
                result = subprocess.run(
                    ['wmic', 'computersystem', 'get', 'TotalPhysicalMemory'],
                    capture_output=True, text=True, timeout=10
                )
                lines = [l.strip() for l in result.stdout.strip().split('\n') if l.strip().isdigit()]
                if lines:
                    info['memory_total_gb'] = int(lines[0]) / (1024 ** 3)
                    
            elif system == 'Linux':
                # Linux: /proc/cpuinfo 和 /proc/meminfo
                with open('/proc/cpuinfo') as f:
                    cores = sum(1 for line in f if line.startswith('processor'))
                    info['cpu_cores'] = cores or 4
                
                with open('/proc/meminfo') as f:
                    for line in f:
                        if line.startswith('MemTotal'):
                            kb = int(line.split()[1])
                            info['memory_total_gb'] = kb / (1024 ** 2)
                        elif line.startswith('MemAvailable'):
                            kb = int(line.split()[1])
                            info['memory_available_gb'] = kb / (1024 ** 2)
                            
            elif system == 'Darwin':
                # macOS: sysctl
                result = subprocess.run(
                    ['sysctl', '-n', 'hw.ncpu'],
                    capture_output=True, text=True, timeout=10
                )
                info['cpu_cores'] = int(result.stdout.strip() or 4)
                
                result = subprocess.run(
                    ['sysctl', '-n', 'hw.memsize'],
                    capture_output=True, text=True, timeout=10
                )
                info['memory_total_gb'] = int(result.stdout.strip()) / (1024 ** 3)
        except Exception as e:
            logger.warning(f"硬件检测回退方案失败: {e}，使用默认值")
    
    def _detect_gpu(self, info: Dict[str, Any]):
        """检测 GPU 信息"""
        import subprocess
        import platform
        
        system = platform.system()
        
        try:
            if system == 'Windows':
                # Windows: wmic path win32_videocontroller get name,AdapterRAM
                result = subprocess.run(
                    ['wmic', 'path', 'win32_videocontroller', 'get', 'name,AdapterRAM'],
                    capture_output=True, text=True, timeout=15
                )
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # 跳过表头
                    parts = line.strip().rsplit(None, 1)
                    if len(parts) == 2 and parts[0].strip():
                        gpu_name = parts[0].strip()
                        # 过滤集成显卡
                        if not any(keyword in gpu_name.lower() for keyword in 
                                   ['intel', 'basic', 'standard', 'microsoft']):
                            info['has_gpu'] = True
                            info['gpu_name'] = gpu_name
                            try:
                                gpu_mem_bytes = int(parts[1].strip())
                                info['gpu_memory_gb'] = gpu_mem_bytes / (1024 ** 3)
                            except (ValueError, IndexError):
                                info['gpu_memory_gb'] = 4.0  # 默认值
                            break
                            
            elif system == 'Linux':
                # Linux: lspci 或 nvidia-smi
                try:
                    result = subprocess.run(
                        ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        parts = result.stdout.strip().split(',')
                        if len(parts) >= 2:
                            info['has_gpu'] = True
                            info['gpu_name'] = parts[0].strip()
                            info['gpu_memory_gb'] = float(parts[1].strip()) / 1024
                except FileNotFoundError:
                    # 尝试 lspci
                    result = subprocess.run(
                        ['lspci'], capture_output=True, text=True, timeout=10
                    )
                    for line in result.stdout.split('\n'):
                        if 'VGA' in line or '3D' in line:
                            if not 'Intel' in line:
                                info['has_gpu'] = True
                                info['gpu_name'] = line.split(':')[-1].strip()
                                info['gpu_memory_gb'] = 4.0  # 未知显存
                                break
                            
            elif system == 'Darwin':
                # macOS: 检查 Metal GPU
                result = subprocess.run(
                    ['system_profiler', 'SPDisplaysDataType'],
                    capture_output=True, text=True, timeout=10
                )
                for line in result.stdout.split('\n'):
                    if 'Chipset Model:' in line and 'Intel' not in line and 'Apple M' in line:
                        info['has_gpu'] = True
                        info['gpu_name'] = line.split(':')[-1].strip()
                        info['gpu_memory_gb'] = 8.0  # Apple Silicon 共享内存
                        break
        except Exception as e:
            logger.warning(f"GPU 检测失败: {e}，使用默认值")
    
    def _read_cache(self) -> Optional[Dict[str, Any]]:
        """读取缓存的硬件信息"""
        try:
            if HARDWARE_CACHE_PATH.exists():
                with open(HARDWARE_CACHE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 检查缓存是否过期
                cache_age = time.time() - data.get('detected_at', 0)
                if cache_age < CACHE_TTL_SECONDS:
                    return data
        except Exception as e:
            logger.debug(f"读取硬件缓存失败: {e}")
        return None
    
    def _write_cache(self, info: Dict[str, Any]):
        """写入硬件信息缓存"""
        try:
            HARDWARE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(HARDWARE_CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug(f"写入硬件缓存失败: {e}")


def main():
    """命令行检测入口"""
    import sys
    
    print("=" * 50)
    print("🖥️  硬件检测")
    print("=" * 50)
    
    detector = HardwareDetector()
    info = detector.detect(force_refresh='--refresh' in sys.argv)
    config = detector.get_optimal_config(info)
    
    print(f"\n硬件信息:")
    print(f"  CPU 核心数: {info['cpu_cores']}")
    print(f"  CPU 频率: {info['cpu_freq_mhz']:.0f} MHz")
    print(f"  内存总量: {info['memory_total_gb']:.1f} GB")
    print(f"  可用内存: {info['memory_available_gb']:.1f} GB")
    
    gpu_status = info['gpu_name'] if info['has_gpu'] else '无独立 GPU'
    print(f"  GPU: {gpu_status}")
    if info['has_gpu']:
        print(f"  显存: {info['gpu_memory_gb']:.1f} GB")
    
    print(f"\n性能配置:")
    print(f"  硬件等级: {config['hardware_tier']}")
    print(f"  OCR 并行页数: {config['ocr_batch_size']}")
    print(f"  OCR 使用 GPU: {'是' if config['ocr_use_gpu'] else '否'}")
    print(f"  LLM 超时: {config['llm_timeout']}s")
    print(f"  最大并发审查数: {config['max_concurrent_reviews']}")
    print(f"  文本分块: {config['text_chunk_size']} 字符")


if __name__ == '__main__':
    main()
