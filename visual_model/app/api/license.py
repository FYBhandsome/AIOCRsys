#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
授权验证API路由 - FastAPI版本
"""
from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timezone

from app.models.license import (
    LicenseVerifyRequest,
    LicenseVerifyResponse,
    TokenResponse,
    SystemInfoResponse,
    NetworkStatusResponse,
    HealthCheckResponse,
    PersistentLicenseCheckResponse,
    PersistentLicenseSaveRequest,
    PersistentLicenseSaveResponse,
    StorageInfoResponse,
    OnlineVerifyRequest
)
from app.services.license_service import license_service, get_mac_addresses, verify_license_base, DEFAULT_PUBLIC_KEY_PEM
from app.core.logger import logger

router = APIRouter(prefix="/license", tags=["授权验证"])


@router.post("/verify", response_model=LicenseVerifyResponse)
async def verify_license(request: LicenseVerifyRequest):
    """
    验证授权码 API 接口（智能模式）
    
    默认使用离线验证，在线验证作为备选
    接收授权码和强制 Token，进行智能验证
    """
    try:
        # 验证输入
        if not request.license.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License 字符串不能为空"
            )
        
        if not request.token.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token 验证码不能为空（现在是强制性的）"
            )
        
        # 执行智能验证
        result = license_service.verify_license(
            request.license.strip(),
            request.token.strip(),
            request.prefer_offline
        )
        
        # 返回验证结果
        if result["valid"]:
            response_data = {
                "valid": True,
                "customer": result.get("customer"),
                "expires_at": result["expires_at"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(result.get("expires_at"), datetime) else str(result.get("expires_at")),
                "issued_at": result["issued_at"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(result.get("issued_at"), datetime) else str(result.get("issued_at")),
                "verification_mode": result.get("verification_mode", "unknown")
            }
            # 如果有备用验证的错误信息，也返回
            if "offline_error" in result:
                response_data["offline_error"] = result["offline_error"]
            if "online_error" in result:
                response_data["online_error"] = result["online_error"]
            
            logger.info(f"授权验证成功: {result.get('customer')}, 模式: {result.get('verification_mode')}")
            return LicenseVerifyResponse(**response_data)
        else:
            logger.warning(f"授权验证失败: {result.get('reason')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "valid": False,
                    "reason": result["reason"],
                    "verification_mode": result.get("verification_mode", "failed"),
                    "key_source": result.get("key_source", "failed"),
                    "key_scheme": "fixed_key_pair"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"授权验证异常: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证失败: {str(e)}"
        )


@router.get("/token", response_model=TokenResponse)
async def get_token():
    """
    获取当前时间的 Token API 接口
    
    Returns:
        JSON: 包含当前 Token 的响应
    """
    try:
        result = license_service.get_current_token()
        if result.get("token"):
            return TokenResponse(token=result["token"])
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"token": None, "reason": result.get("reason", "未知错误")}
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Token失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"token": None, "reason": str(e)}
        )


@router.post("/verify-online", response_model=LicenseVerifyResponse)
async def verify_online(request: OnlineVerifyRequest):
    """
    在线验证 API 接口
    
    调用独立生成端系统的验证接口进行在线验证
    如果网络不可用，建议使用离线验证
    """
    try:
        # 验证输入
        if not request.license.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License 字符串不能为空"
            )
        
        # 执行在线验证
        result = license_service.verify_online(request.license.strip())
        
        # 返回验证结果
        if result["valid"]:
            return LicenseVerifyResponse(**result)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"valid": False, "reason": result["reason"]}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"在线验证失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"在线验证失败: {str(e)}"
        )


@router.get("/system-info", response_model=SystemInfoResponse)
async def get_system_info():
    """
    获取系统信息 API 接口
    
    Returns:
        JSON: 系统信息
    """
    try:
        info = license_service.get_system_info()
        return SystemInfoResponse(**info)
    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/network-status", response_model=NetworkStatusResponse)
async def get_network_status():
    """
    获取网络连接状态
    
    Returns:
        JSON: 网络状态信息
    """
    try:
        network_status = license_service.check_network_connectivity()
        return NetworkStatusResponse(
            network_status=network_status,
            recommended_mode="offline" if not network_status["connected"] else "online",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"获取网络状态失败: {str(e)}", exc_info=True)
        return NetworkStatusResponse(
            network_status={"connected": False, "error": str(e)},
            recommended_mode="offline",
            timestamp=datetime.now(timezone.utc).isoformat()
        )


@router.get("/health", response_model=HealthCheckResponse)
async def license_health_check():
    """
    授权系统健康检查
    
    Returns:
        JSON: 健康状态
    """
    try:
        # 检查基本功能
        mac_addresses = get_mac_addresses()
        
        # 尝试获取公钥（这会测试独立生成端系统API连接）
        try:
            public_key = license_service.get_public_key()
            public_key_available = bool(public_key)
            # 比较是否为默认公钥
            key_source = "default" if public_key == DEFAULT_PUBLIC_KEY_PEM else "remote"
            generator_status = "connected" if key_source == "remote" else "using_default_key"
        except Exception as e:
            public_key_available = False
            key_source = "failed"
            generator_status = f"disconnected: {str(e)}"
        
        # 检查网络状态
        network_status = license_service.check_network_connectivity()
        
        return HealthCheckResponse(
            status="healthy" if public_key_available else "unhealthy",
            mac_addresses_available=len(mac_addresses) > 0,
            public_key_available=public_key_available,
            key_source=key_source,
            key_scheme="fixed_key_pair",
            generator_status=generator_status,
            network_status=network_status,
            recommended_verification_mode="offline" if not network_status["connected"] else "online"
        )
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}", exc_info=True)
        return HealthCheckResponse(
            status="unhealthy",
            error=str(e)
        )


@router.get("/persistent/check", response_model=PersistentLicenseCheckResponse)
async def check_persistent_license():
    """
    检查持久化授权状态 API 接口
    
    Returns:
        JSON: 持久化授权检查结果
    """
    try:
        result = license_service.check_persistent_license()
        
        if result.get("valid"):
            response_data = {
                "valid": True,
                "customer": result.get("customer"),
                "verification_mode": result.get("verification_mode", "offline"),
                "key_source": result.get("key_source", "default"),
                "key_scheme": "fixed_key_pair"
            }
            # 如果有过期时间，格式化后返回
            if result.get("expires_at"):
                if isinstance(result["expires_at"], datetime):
                    response_data["expires_at"] = result["expires_at"].strftime("%Y-%m-%d %H:%M:%S")
                else:
                    response_data["expires_at"] = str(result["expires_at"])
            if result.get("issued_at"):
                if isinstance(result["issued_at"], datetime):
                    response_data["issued_at"] = result["issued_at"].strftime("%Y-%m-%d %H:%M:%S")
                else:
                    response_data["issued_at"] = str(result["issued_at"])
            return PersistentLicenseCheckResponse(**response_data)
        else:
            # 对于"未找到授权"等非异常情况，返回200并携带valid=false，减少前端告警噪声
            return PersistentLicenseCheckResponse(
                valid=False,
                reason=result.get("reason", "授权验证失败")
            )
            
    except Exception as e:
        logger.error(f"检查持久化授权失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"valid": False, "reason": f"检查持久化授权时发生错误: {str(e)}"}
        )


@router.post("/persistent/save", response_model=PersistentLicenseSaveResponse)
async def save_persistent_license(request: PersistentLicenseSaveRequest):
    """
    保存授权码到持久化存储 API 接口
    
    Request Body:
        license: 授权码字符串
        token: Token验证码
        
    Returns:
        JSON: 保存结果
    """
    try:
        # 验证输入
        if not request.license.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "reason": "License 字符串不能为空"}
            )
        
        # Token 允许为空：持久化仅用于后续免输验证
        
        # 先验证授权码是否有效（仅签名/时间/MAC，不强制Token）
        # 放宽以便在用户已有一次成功验证后保存到持久化
        try:
            public_key_pem = license_service.get_public_key()
            tmp_result = verify_license_base(request.license.strip(), public_key_pem)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "reason": f"授权校验失败: {str(e)}"}
            )
        if not tmp_result.get("valid"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "reason": f"授权码验证失败，无法保存: {tmp_result.get('reason', '未知错误')}"
                }
            )
        
        # 保存到持久化存储
        result = license_service.save_persistent_license(request.license.strip(), request.token.strip())
        
        if result.get("success"):
            logger.info("授权码已保存到持久化存储")
            return PersistentLicenseSaveResponse(
                success=True,
                message="授权码已成功保存到持久化存储"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "reason": result.get("reason", "保存失败")
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存持久化授权失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "reason": f"保存持久化授权时发生错误: {str(e)}"}
        )


@router.post("/persistent/clear", response_model=PersistentLicenseSaveResponse)
async def clear_persistent_license():
    """
    清除持久化授权 API 接口
    
    Returns:
        JSON: 清除结果
    """
    try:
        result = license_service.clear_persistent_license()
        
        if result.get("success"):
            logger.info("持久化授权已清除")
            return PersistentLicenseSaveResponse(
                success=True,
                message="持久化授权已成功清除"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "reason": result.get("reason", "清除失败")
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清除持久化授权失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "reason": f"清除持久化授权时发生错误: {str(e)}"}
        )


@router.get("/storage-info", response_model=StorageInfoResponse)
async def get_storage_info():
    """
    获取授权存储的详细信息（目录、文件存在与大小、记录条数等）
    """
    try:
        info = license_service.get_storage_info()
        return StorageInfoResponse(**info)
    except Exception as e:
        logger.error(f"获取存储信息失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"获取存储信息失败: {str(e)}"}
        )

