#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
授权管理服务
提供授权码验证、Token生成、持久化等功能
"""

import base64
import logging
import hashlib
import json
import os
import uuid
import subprocess
from datetime import datetime, timedelta
from typing import Tuple, List, Optional, Dict, Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import requests

# 配置参数
GENERATOR_URL = "http://localhost:5001"  # 独立生成端系统地址

# 默认公钥配置（固定密钥对方案）
DEFAULT_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuof3XIc4yslbKqxLXnSa
02c+lkkImkUwJ0gqBGaAkb3S9e/dPFKzWHW7NfiY0lNoPv3F2NDXqgcjIBLpbhQp
fOMffeC581A6aBK1dKALkOSINVyZafkhpE7rXd8USvsPCZx0dD0705oMEowg7rTa
5oN1Rxgaee+AXmeexWFxNzhVBCOY9Nez72MylseExzRr2gf6t6P6CJpg5tA37D0m
JH5Pi7BN+YGkvYka/J4gVJvEjmV8ga2tfPSa4bz1/wiptqwvR94lLW5fvxMTX6hx
XbBvKP7P+5uReuGNyGO2kRJEzWJkax2GHgy+v77vi84cv1QPwFVXh6RqOHxx5d31
7QIDAQAB
-----END PUBLIC KEY-----"""

# 公钥缓存
PUBLIC_KEY_PEM = None
logger = logging.getLogger(__name__)


def _canonicalize_mac_string(value: str) -> str:
    """
    将任意形式的 MAC 字符串规范化为小写冒号分隔：xx:xx:xx:xx:xx:xx。
    支持：
    - 00:11:22:33:44:55 / 00-11-22-33-44-55
    - 001122334455（无分隔符）
    - 00,11,22,33,44,55（逗号分隔六段）
    无法解析时返回空串。
    """
    try:
        import re
        value = (value or "").strip()
        if not value:
            return ""

        # 仅十六进制字符
        hex_only = re.sub(r"[^0-9A-Fa-f]", "", value)
        if len(hex_only) == 12 and re.fullmatch(r"[0-9A-Fa-f]{12}", hex_only):
            parts = [hex_only[i:i+2] for i in range(0, 12, 2)]
            return ":".join(p.lower() for p in parts)

        # 逗号分隔六段
        if re.fullmatch(r"\s*([0-9A-Fa-f]{1,2}\s*,\s*){5}[0-9A-Fa-f]{1,2}\s*", value):
            parts = [p.strip() for p in value.split(",")]
            parts = [f"{int(p, 16):02x}" for p in parts]
            return ":".join(parts)

        # 冒号/短横/空格分隔
        candidate = value.replace("-", ":").replace(" ", ":").strip(":")
        segs = [s for s in candidate.split(":") if s != ""]
        import re as _re
        if len(segs) == 6 and all(_re.fullmatch(r"[0-9A-Fa-f]{1,2}", s or "") for s in segs):
            parts = [f"{int(s, 16):02x}" for s in segs]
            return ":".join(parts)

        return ""
    except Exception:
        return ""


def _normalize_mac_list(values) -> list:
    """将字符串或列表中的 MAC 统一规范化并去重，返回列表。
    兼容历史格式：当列表恰好为六段一字节十六进制（例如 ["00","FF",...]）时，合并为一个 MAC。
    """
    if values is None:
        return []
    if isinstance(values, str):
        canon = _canonicalize_mac_string(values)
        return [canon] if canon else []

    # values 是列表时
    result = []
    seen = set()
    # 1) 历史兼容：六段一字节十六进制
    try:
        import re as _re
        if (
            isinstance(values, list)
            and len(values) == 6
            and all(isinstance(x, str) and _re.fullmatch(r"[0-9A-Fa-f]{1,2}", (x or "")) for x in values)
        ):
            merged = ":".join(f"{int(x, 16):02x}" for x in values)
            c = _canonicalize_mac_string(merged)
            if c:
                return [c]
    except Exception:
        pass

    # 2) 常规：逐个规范化
    for v in values:
        if not isinstance(v, str):
            continue
        c = _canonicalize_mac_string(v)
        if c and c not in seen:
            seen.add(c)
            result.append(c)
    return result


def get_mac_addresses() -> List[str]:
    """
    获取本机所有 MAC 地址
    
    尝试通过系统命令获取网络接口的 MAC 地址
    如果获取失败，返回默认的 MAC 地址
    
    Returns:
        List[str]: MAC 地址列表
    """
    macs = []
    try:
        # Windows 系统：使用 ipconfig 命令获取 MAC 地址
        result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True, encoding='gbk')
        
        # 解析命令输出，查找 MAC 地址
        for line in result.stdout.split('\n'):
            # 查找包含 "Physical Address" 或 "MAC Address" 的行
            if 'Physical Address' in line or 'MAC Address' in line:
                # 提取 MAC 地址并格式化
                mac = line.split(':')[-1].strip().replace('-', ':').lower()
                # 验证 MAC 地址格式（17 个字符，包含冒号）
                if mac and len(mac) == 17:
                    macs.append(mac)
    except:
        # 如果获取失败，忽略异常
        pass
    
    # 如果获取失败，返回一个默认值
    if not macs:
        macs = ["00:11:22:33:44:55"]
    
    # 再做一次严格规范化去重
    normalized = []
    seen = set()
    for m in macs:
        c = _canonicalize_mac_string(m)
        if c and c not in seen:
            seen.add(c)
            normalized.append(c)
    return normalized


def get_public_key() -> str:
    """
    获取公钥，优先使用默认公钥，失败时尝试从独立生成端系统获取
    
    Returns:
        str: PEM 格式的公钥字符串
        
    Raises:
        Exception: 当无法获取公钥时抛出异常
    """
    global PUBLIC_KEY_PEM
    if PUBLIC_KEY_PEM is None:
        # 优先使用默认公钥（固定密钥对方案）
        if DEFAULT_PUBLIC_KEY_PEM:
            PUBLIC_KEY_PEM = DEFAULT_PUBLIC_KEY_PEM
        else:
            # 如果默认公钥不存在，尝试从独立生成端系统获取
            try:
                response = requests.get(f"{GENERATOR_URL}/api/public-key", timeout=5)
                if response.status_code == 200:
                    PUBLIC_KEY_PEM = response.json()["publicKeyPem"]
                else:
                    raise Exception(f"独立生成端系统未提供公钥接口，状态码: {response.status_code}")
            except requests.exceptions.RequestException as e:
                raise Exception(f"无法连接到独立生成端系统API ({GENERATOR_URL}): {str(e)}")
            except Exception as e:
                raise Exception(f"获取公钥失败: {str(e)}")
    
    if not PUBLIC_KEY_PEM:
        raise Exception("公钥获取失败，无法进行授权验证")
        
    return PUBLIC_KEY_PEM


def aes_decrypt(aes_key: bytes, enc: bytes) -> bytes:
    """
    使用 AES-GCM 模式解密数据
    
    Args:
        aes_key: 16 字节的 AES 密钥
        enc: 加密数据，格式为 nonce(12字节) + ciphertext + tag(16字节)
        
    Returns:
        bytes: 解密后的明文数据
    """
    # 分离 nonce 和加密数据
    nonce, ct_tag = enc[:12], enc[12:]
    
    # 创建 AES-GCM 解密器
    aesgcm = AESGCM(aes_key)
    
    # 执行解密
    return aesgcm.decrypt(nonce, ct_tag, None)


def rsa_verify(public_key: rsa.RSAPublicKey, data: bytes, signature: bytes) -> bool:
    """
    使用 RSA 公钥验证签名
    
    Args:
        public_key: RSA 公钥对象
        data: 原始数据
        signature: 签名数据
        
    Returns:
        bool: 验证成功返回 True，失败返回 False
    """
    try:
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),  # 使用 SHA256 作为掩码生成函数
                salt_length=padding.PSS.MAX_LENGTH   # 使用最大盐长度
            ),
            hashes.SHA256(),  # 使用 SHA256 哈希算法
        )
        return True
    except Exception:
        return False


def parse_license(lic: str) -> Tuple[bytes, bytes, bytes]:
    """
    解析授权码字符串，提取各个组件
    
    Args:
        lic: 授权码字符串
        
    Returns:
        Tuple[bytes, bytes, bytes]: (aes_key, enc_data, signature)
        
    Raises:
        ValueError: 当授权码格式不正确时抛出异常
    """
    # 按 | 分隔符分割授权码
    aes_b64, hexlen, enc_b64, sig_b64 = lic.split("|")
    
    # 解码各个组件
    aes_key = base64.b64decode(aes_b64)      # AES 密钥
    enc_data = base64.b64decode(enc_b64)     # 加密数据
    sig = base64.b64decode(sig_b64)          # 签名
    
    # 验证加密数据长度是否正确
    if int(hexlen, 16) != len(enc_data):
        raise ValueError("enc_data length mismatch")
    
    return aes_key, enc_data, sig


def verify_token(payload: dict, token: str, current_time: datetime) -> dict:
    """
    验证 Token 的完整流程
    
    强制要求：必须在指定时间窗口内，且Token在1个月内有效
    
    Args:
        payload: 授权码载荷数据
        token: 用户提供的 Token
        current_time: 当前时间
        
    Returns:
        dict: Token 验证结果
    """
    try:
        # 1. 检查是否在指定的时间窗口内（精确到分钟，放宽±1分钟容差）
        token_hour = payload.get("tokenHour")
        token_minute = payload.get("tokenMinute")
        if token_hour is None or token_minute is None:
            return {"valid": False, "reason": "授权载荷缺少Token时间窗口信息"}

        same_minute = (current_time.hour == token_hour and current_time.minute == token_minute)
        prev_minute = (current_time.hour == token_hour and current_time.minute == (token_minute + 1) % 60)
        next_minute = (current_time.hour == token_hour and (token_minute == (current_time.minute + 1) % 60))
        if not (same_minute or prev_minute or next_minute):
            return {"valid": False, "reason": "不在Token验证时间窗口内，请在指定时间使用"}
        
        # 2. 检查 Token 有效期（强制限制为1个月）
        # 确保时区一致性：将issued_date转换为与current_time相同的时区
        from datetime import timezone, timedelta
        beijing_tz = timezone(timedelta(hours=8))
        issued_date = datetime.fromtimestamp(payload.get("issuedTime", 0), tz=beijing_tz)
        days_diff = (current_time - issued_date).days
        
        # 强制限制Token有效期为30天
        if days_diff > 30:
            return {"valid": False, "reason": "Token已超过1个月有效期，请重新申请授权"}
        
        # 3. 生成期望的 Token 候选集（授权内所有 MAC；若未绑定 MAC，则允许空串与本机 MAC）
        # 精确到分钟：时间戳格式 YYYYMMDDHHMM
        minute_stamp = current_time.strftime("%Y%m%d%H%M")
        mac_field = payload.get("mac")

        # 允许未绑定（空串）参与 Token 计算
        candidate_macs = _normalize_mac_list(mac_field)
        if not candidate_macs:
            candidate_macs = [""]
        
        # 若未绑定（候选仅为空串），允许加入本机第一块MAC以提升可用性
        if candidate_macs == [""]:
            try:
                local_macs = get_mac_addresses()
                if local_macs:
                    candidate_macs.append(local_macs[0])
            except Exception:
                pass

        # 4. 比较 Token（不区分大小写），任一匹配即通过
        provided = token.lower()
        for mac_value in candidate_macs:
            expected = hashlib.sha256(f"{minute_stamp}{mac_value}".encode()).hexdigest()[:6]
            if provided == expected.lower():
                return {"valid": True}

        return {"valid": False, "reason": "Token验证码错误，请重新获取"}
        
    except Exception as e:
        return {"valid": False, "reason": f"Token验证失败: {str(e)}"}


def verify_license(license_str: str, public_key_pem: str, token: Optional[str] = None) -> dict:
    """
    验证授权码的完整流程
    
    包括签名验证、解密、MAC 地址验证、时间验证和强制 Token 验证
    
    Args:
        license_str: 授权码字符串
        public_key_pem: PEM 格式的公钥字符串
        token: 必须提供的 Token 验证码
        
    Returns:
        dict: 验证结果字典
            - valid: bool - 验证是否成功
            - reason: str - 失败原因（如果验证失败）
            - customer: str - 客户名称（如果验证成功）
            - expires_at: datetime - 过期时间（如果验证成功）
            - issued_at: datetime - 签发时间（如果验证成功）
    """
    try:
        # 1. 加载公钥
        public_key = serialization.load_pem_public_key(public_key_pem.encode())
        
        # 2. 解析授权码
        aes_key, enc_data, sig = parse_license(license_str)
        
        # 3. 验证 RSA 签名
        if not rsa_verify(public_key, enc_data, sig):
            return {"valid": False, "reason": "签名验证失败"}
        
        # 4. 使用 AES 密钥解密数据
        plaintext = aes_decrypt(aes_key, enc_data).decode()
        payload = json.loads(plaintext)
        
        # 5. 验证 MAC 地址（可选）
        license_macs_raw = payload.get("mac")
        
        # 如果授权码中没有MAC地址或MAC地址为空，则跳过MAC地址验证
        if license_macs_raw is None or (isinstance(license_macs_raw, list) and len(license_macs_raw) == 0) or (isinstance(license_macs_raw, str) and license_macs_raw.strip() == ""):
            # MAC地址为空，跳过验证
            pass
        else:
            # 有MAC地址，进行验证
            current_macs = get_mac_addresses()
            license_macs = _normalize_mac_list(license_macs_raw)
            # 规范化后的集合求交
            mac_match = any(m in set(license_macs) for m in set(current_macs))
            if not mac_match:
                return {"valid": False, "reason": "MAC地址不匹配"}
        
        # 7. 验证时间
        # 使用北京时间进行验证，与生成端保持一致
        from datetime import timezone, timedelta
        beijing_tz = timezone(timedelta(hours=8))
        now = datetime.now(beijing_tz)
        now_timestamp = int(now.timestamp())
        
        # 检查授权是否已生效
        if now_timestamp < payload.get("notBefore", 0):
            return {"valid": False, "reason": "授权尚未生效"}
        
        # 检查授权是否已过期
        if now_timestamp > payload.get("notAfter", 0):
            return {"valid": False, "reason": "授权已过期"}
        
        # 8. 强制 Token 验证（必须提供）
        if not token:
            return {"valid": False, "reason": "必须提供Token验证码"}
        
        token_result = verify_token(payload, token, now)
        if not token_result["valid"]:
            return token_result
        
        # 9. 验证成功，返回详细信息
        # 确保返回的时间对象使用正确的时区
        from datetime import timezone, timedelta
        beijing_tz = timezone(timedelta(hours=8))
        return {
            "valid": True,
            "payload": payload,
            "customer": payload.get("customer"),
            "expires_at": datetime.fromtimestamp(payload.get("notAfter", 0), tz=beijing_tz),
            "issued_at": datetime.fromtimestamp(payload.get("issuedTime", 0), tz=beijing_tz)
        }
        
    except Exception as e:
        return {"valid": False, "reason": f"验证失败: {str(e)}"}


def verify_license_base(license_str: str, public_key_pem: str) -> dict:
    """
    基础授权验证：签名、解密、MAC、有效期检查，不包含 Token 校验。
    用于持久化保存与启动时免输验证。
    """
    try:
        # 1. 加载公钥
        public_key = serialization.load_pem_public_key(public_key_pem.encode())

        # 2. 解析授权码
        aes_key, enc_data, sig = parse_license(license_str)

        # 3. 验证 RSA 签名
        if not rsa_verify(public_key, enc_data, sig):
            return {"valid": False, "reason": "签名验证失败"}

        # 4. 解密
        plaintext = aes_decrypt(aes_key, enc_data).decode()
        payload = json.loads(plaintext)

        # 5. MAC 校验（同 verify_license）
        license_macs_raw = payload.get("mac")
        if license_macs_raw is None or (isinstance(license_macs_raw, list) and len(license_macs_raw) == 0) or (isinstance(license_macs_raw, str) and license_macs_raw.strip() == ""):
            pass
        else:
            current_macs = get_mac_addresses()
            if isinstance(license_macs_raw, str):
                license_macs = [license_macs_raw]
            else:
                license_macs = license_macs_raw or []
            mac_match = any(mac in license_macs for mac in current_macs)
            if not mac_match:
                return {"valid": False, "reason": "MAC地址不匹配"}

        # 6. 时间窗口（北京时间）
        from datetime import timezone, timedelta
        beijing_tz = timezone(timedelta(hours=8))
        now = datetime.now(beijing_tz)
        now_timestamp = int(now.timestamp())
        if now_timestamp < payload.get("notBefore", 0):
            return {"valid": False, "reason": "授权尚未生效"}
        if now_timestamp > payload.get("notAfter", 0):
            return {"valid": False, "reason": "授权已过期"}

        return {
            "valid": True,
            "payload": payload,
            "customer": payload.get("customer"),
            "expires_at": datetime.fromtimestamp(payload.get("notAfter", 0), tz=beijing_tz),
            "issued_at": datetime.fromtimestamp(payload.get("issuedTime", 0), tz=beijing_tz)
        }
    except Exception as e:
        return {"valid": False, "reason": f"基础验证失败: {str(e)}"}


def generate_token(mac: str) -> str:
    """
    生成当前时间的 Token
    
    Args:
        mac: MAC 地址
        
    Returns:
        str: 6 位十六进制 Token
    """
    # 获取当前北京时间，与生成端保持一致
    from datetime import timezone, timedelta
    beijing_tz = timezone(timedelta(hours=8))
    current_time = datetime.now(beijing_tz)
    
    # 精确到分钟的时间戳 YYYYMMDDHHMM
    minute_stamp = current_time.strftime("%Y%m%d%H%M")
    
    # 生成 Token：sha256(分钟时间戳 + 规范化MAC) 的前 6 位
    mac_canon = _canonicalize_mac_string(mac)
    return hashlib.sha256(f"{minute_stamp}{mac_canon}".encode()).hexdigest()[:6]


def verify_license_online(license_str: str) -> dict:
    """
    在线验证 API 接口
    
    调用独立生成端系统的验证接口进行在线验证
    如果网络不可用，建议使用离线验证
    
    Args:
        license_str: 授权码字符串
        
    Returns:
        dict: 在线验证结果
    """
    try:
        # 验证输入
        if not license_str:
            return {"valid": False, "reason": "License 字符串不能为空"}
        
        # 调用独立生成端系统的验证接口
        response = requests.post(
            f"{GENERATOR_URL}/api/verify",
            json={"license": license_str},
            timeout=10
        )
        
        # 处理响应
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            return {"valid": False, "reason": "在线验证失败"}
            
    except requests.exceptions.RequestException:
        # 网络连接失败
        return {"valid": False, "reason": "网络连接失败，请使用离线验证"}
    except Exception as e:
        return {"valid": False, "reason": f"在线验证失败: {str(e)}"}


class LicenseService:
    """授权服务类 - FastAPI版本"""
    
    def __init__(self, generator_url: str = GENERATOR_URL):
        self.generator_url = generator_url
        self.public_key = None
    
    def get_public_key(self) -> str:
        """获取公钥"""
        if self.public_key is None:
            self.public_key = get_public_key()
        return self.public_key
    
    def verify_license(self, license_str: str, token: str, prefer_offline: bool = True) -> dict:
        """
        智能验证授权码（固定密钥对方案）
        
        Args:
            license_str: 授权码字符串
            token: Token验证码
            prefer_offline: 是否优先使用离线验证（默认True）
            
        Returns:
            dict: 验证结果，包含验证模式信息
        """
        if prefer_offline:
            # 优先尝试离线验证（固定密钥对方案）
            try:
                public_key = self.get_public_key()
                result = verify_license(license_str, public_key, token)
                result["verification_mode"] = "offline"
                result["key_source"] = "default"  # 标识使用默认公钥
                return result
            except Exception as e:
                # 离线验证失败，尝试在线验证
                try:
                    online_result = self.verify_online(license_str)
                    online_result["verification_mode"] = "online"
                    online_result["offline_error"] = str(e)
                    online_result["key_source"] = "remote"  # 标识使用远程公钥
                    return online_result
                except Exception as online_e:
                    # 在线验证也失败，返回离线验证的错误
                    return {
                        "valid": False,
                        "reason": f"离线验证失败: {str(e)}, 在线验证也失败: {str(online_e)}",
                        "verification_mode": "failed",
                        "key_source": "failed"
                    }
        else:
            # 优先尝试在线验证
            try:
                online_result = self.verify_online(license_str)
                online_result["verification_mode"] = "online"
                online_result["key_source"] = "remote"
                return online_result
            except Exception as e:
                # 在线验证失败，尝试离线验证
                try:
                    public_key = self.get_public_key()
                    result = verify_license(license_str, public_key, token)
                    result["verification_mode"] = "offline"
                    result["online_error"] = str(e)
                    result["key_source"] = "default"
                    return result
                except Exception as offline_e:
                    # 离线验证也失败，返回在线验证的错误
                    return {
                        "valid": False,
                        "reason": f"在线验证失败: {str(e)}, 离线验证也失败: {str(offline_e)}",
                        "verification_mode": "failed",
                        "key_source": "failed"
                    }
    
    def get_current_token(self) -> dict:
        """获取当前Token"""
        try:
            mac_addresses = get_mac_addresses()
            if mac_addresses:
                token = generate_token(mac_addresses[0])
                return {"token": token}
            else:
                return {"token": None, "reason": "无法获取 MAC 地址"}
        except Exception as e:
            return {"token": None, "reason": str(e)}
    
    def verify_online(self, license_str: str) -> dict:
        """在线验证"""
        return verify_license_online(license_str)
    
    def check_network_connectivity(self) -> dict:
        """
        检查网络连接状态
        
        Returns:
            dict: 网络连接状态信息
        """
        try:
            # 尝试连接独立生成端系统API的健康检查接口
            response = requests.get(f"{self.generator_url}/api/health", timeout=3)
            return {
                "connected": response.status_code == 200,
                "response_time": response.elapsed.total_seconds(),
                "status_code": response.status_code
            }
        except requests.exceptions.RequestException as e:
            return {
                "connected": False,
                "error": str(e),
                "response_time": None,
                "status_code": None
            }
    
    def get_system_info(self) -> dict:
        """获取系统信息"""
        network_status = self.check_network_connectivity()
        
        # 检查公钥状态
        try:
            public_key = self.get_public_key()
            public_key_available = bool(public_key)
            key_source = "default" if public_key == DEFAULT_PUBLIC_KEY_PEM else "remote"
        except Exception:
            public_key_available = False
            key_source = "failed"
        
        return {
            "mac_addresses": get_mac_addresses(),
            "current_time": datetime.utcnow().isoformat(),
            "network_status": network_status,
            "public_key_available": public_key_available,
            "key_source": key_source,
            "key_scheme": "fixed_key_pair"  # 标识使用固定密钥对方案
        }
    
    def check_persistent_license(self) -> dict:
        """
        检查持久化授权状态
        
        从本地存储中读取并验证授权码
        
        Returns:
            dict: 持久化授权检查结果
                - valid: bool - 是否有有效授权
                - reason: str - 失败原因（如果检查失败）
                - expires_at: datetime - 过期时间（如果有有效授权）
                - customer: str - 客户名称（如果有有效授权）
        """
        try:
            # 检查是否存在持久化授权文件
            persistent_file = os.path.join(os.path.expanduser("~"), ".license_persistent")
            try:
                logger.info(f"[License] 检查持久化授权文件: {persistent_file}")
            except Exception:
                pass
            
            if not os.path.exists(persistent_file):
                try:
                    logger.info("[License] 未找到持久化授权文件")
                except Exception:
                    pass
                return {"valid": False, "reason": "未找到持久化授权文件"}
            
            # 读取持久化授权数据
            with open(persistent_file, 'r', encoding='utf-8') as f:
                persistent_data = json.load(f)
            
            license_str = persistent_data.get("license")
            token = persistent_data.get("token")
            
            if not license_str:
                return {"valid": False, "reason": "持久化授权文件中没有授权码"}
            
            # 验证授权码（持久化校验时不强制Token，以提升可用性）
            try:
                public_key = self.get_public_key()
                base_check = verify_license_base(license_str, public_key)
            except Exception as e:
                return {"valid": False, "reason": f"授权校验失败: {str(e)}"}
            
            if not base_check.get("valid"):
                try:
                    logger.warning(f"[License] 持久化授权基础校验失败: {base_check.get('reason')}")
                except Exception:
                    pass
                return {"valid": False, "reason": base_check.get("reason", "授权验证失败")}
            
            # 基础校验通过，返回有限信息
            result = base_check
            try:
                logger.info("[License] 持久化授权有效：客户=%s, 有效期至=%s", result.get("customer"), result.get("expires_at"))
            except Exception:
                pass
            
            if result.get("valid"):
                # 授权有效，返回详细信息
                return {
                    "valid": True,
                    "expires_at": result.get("expires_at"),
                    "customer": result.get("customer"),
                    "verification_mode": result.get("verification_mode", "unknown")
                }
            else:
                # 授权无效，返回失败原因
                return {
                    "valid": False,
                    "reason": result.get("reason", "授权验证失败")
                }
                
        except Exception as e:
            return {"valid": False, "reason": f"检查持久化授权时发生错误: {str(e)}"}
    
    def save_persistent_license(self, license_str: str, token: str) -> dict:
        """
        保存授权码到持久化存储
        
        Args:
            license_str: 授权码字符串
            token: Token验证码
            
        Returns:
            dict: 保存结果
                - success: bool - 是否保存成功
                - reason: str - 失败原因（如果保存失败）
        """
        try:
            persistent_file = os.path.join(os.path.expanduser("~"), ".license_persistent")
            
            # 创建持久化数据
            # 解出payload，保存解析信息（便于重启后快速读取）
            try:
                public_key = self.get_public_key()
                base = verify_license_base(license_str, public_key)
                payload = base.get("payload", {}) if base.get("valid") else {}
            except Exception:
                payload = {}

            persistent_data = {
                "license": license_str,
                "token": token,
                "saved_at": datetime.utcnow().isoformat(),
                "payload": payload
            }
            
            # 保存到文件
            with open(persistent_file, 'w', encoding='utf-8') as f:
                json.dump(persistent_data, f, ensure_ascii=False, indent=2)
            try:
                logger.info(f"[License] 已保存持久化授权到: {persistent_file}")
            except Exception:
                pass
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "reason": f"保存持久化授权时发生错误: {str(e)}"}
    
    def clear_persistent_license(self) -> dict:
        """
        清除持久化授权
        
        Returns:
            dict: 清除结果
                - success: bool - 是否清除成功
                - reason: str - 失败原因（如果清除失败）
        """
        try:
            persistent_file = os.path.join(os.path.expanduser("~"), ".license_persistent")
            
            if os.path.exists(persistent_file):
                os.remove(persistent_file)
                try:
                    logger.info(f"[License] 已删除持久化授权文件: {persistent_file}")
                except Exception:
                    pass
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "reason": f"清除持久化授权时发生错误: {str(e)}"}

    def get_storage_info(self) -> dict:
        """
        获取授权存储的详细信息（目录、文件存在与大小、记录条数等）
        
        Returns:
            dict: 存储信息
        """
        try:
            # 与持久化路径保持一致
            persistent_file = os.path.join(os.path.expanduser("~"), ".license_persistent")
            storage_dir = os.path.dirname(persistent_file)

            storage_dir_exists = os.path.isdir(storage_dir)
            license_file_exists = os.path.isfile(persistent_file)
            license_file_size = os.path.getsize(persistent_file) if license_file_exists else 0

            verification_records_count = 0
            verification_file_exists = False
            verification_file_size = 0

            # 如果持久化文件存在，尝试读取基本信息并统计验证记录
            if license_file_exists:
                try:
                    with open(persistent_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # 兼容可能存在的验证记录数组
                        records = data.get('verification_records')
                        if isinstance(records, list):
                            verification_records_count = len(records)
                            verification_file_exists = True
                            verification_file_size = license_file_size
                except Exception:
                    pass

            return {
                "storage_dir": storage_dir,
                "storage_dir_exists": storage_dir_exists,
                "license_file_exists": license_file_exists,
                "license_file_size": license_file_size,
                "verification_file_exists": verification_file_exists,
                "verification_file_size": verification_file_size,
                "verification_records_count": verification_records_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"error": f"获取存储信息失败: {str(e)}"}


# 创建全局服务实例
license_service = LicenseService()

