"""
信息预处理模块 - 隐私脱敏
基于第一性原理：自动识别并加密敏感信息
"""
import re
from typing import Dict, Tuple


class PrivacyMask:
    """隐私脱敏器"""
    
    def __init__(self):
        # 手机号
        self.phone_pattern = re.compile(
            r'1[3-9]\d{9}',
            re.IGNORECASE
        )
        
        # 身份证号
        self.id_card_pattern = re.compile(
            r'\d{17}[\dXx]',
            re.IGNORECASE
        )
        
        # 银行卡号
        self.bank_card_pattern = re.compile(
            r'\d{16,19}',
            re.IGNORECASE
        )
        
        # 邮箱
        self.email_pattern = re.compile(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            re.IGNORECASE
        )
        
        # IP地址
        self.ip_pattern = re.compile(
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
            re.IGNORECASE
        )
    
    def mask_phone(self, text: str) -> Tuple[str, int]:
        """脱敏手机号，返回(脱敏文本, 脱敏次数)"""
        count = 0
        
        def replace_phone(match):
            nonlocal count
            phone = match.group()
            count += 1
            # 138****1234
            return f"{phone[:3]}****{phone[-4:]}"
        
        masked_text = self.phone_pattern.sub(replace_phone, text)
        return masked_text, count
    
    def mask_id_card(self, text: str) -> Tuple[str, int]:
        """脱敏身份证号"""
        count = 0
        
        def replace_id(match):
            nonlocal count
            id_card = match.group()
            count += 1
            # 110***********1234
            return f"{id_card[:3]}***********{id_card[-4:]}"
        
        masked_text = self.id_card_pattern.sub(replace_id, text)
        return masked_text, count
    
    def mask_bank_card(self, text: str) -> Tuple[str, int]:
        """脱敏银行卡号"""
        count = 0
        
        def replace_card(match):
            nonlocal count
            card = match.group()
            count += 1
            # **** **** **** 1234
            return f"****{card[-4:]}"
        
        masked_text = self.bank_card_pattern.sub(replace_card, text)
        return masked_text, count
    
    def mask_email(self, text: str) -> Tuple[str, int]:
        """脱敏邮箱"""
        count = 0
        
        def replace_email(match):
            nonlocal count
            email = match.group()
            count += 1
            parts = email.split('@')
            if len(parts[0]) > 2:
                masked = parts[0][:2] + '***' + '@' + parts[1]
            else:
                masked = '***@' + parts[1]
            return masked
        
        masked_text = self.email_pattern.sub(replace_email, text)
        return masked_text, count
    
    def mask_ip(self, text: str) -> Tuple[str, int]:
        """脱敏IP地址"""
        count = 0
        
        def replace_ip(match):
            nonlocal count
            ip = match.group()
            count += 1
            parts = ip.split('.')
            return f"{parts[0]}.***.***.{parts[-1]}"
        
        masked_text = self.ip_pattern.sub(replace_ip, text)
        return masked_text, count
    
    def mask_all(self, text: str) -> Tuple[str, Dict[str, int]]:
        """脱敏所有敏感信息"""
        counts = {}
        
        text, counts['phone'] = self.mask_phone(text)
        text, counts['id_card'] = self.mask_id_card(text)
        text, counts['bank_card'] = self.mask_bank_card(text)
        text, counts['email'] = self.mask_email(text)
        text, counts['ip'] = self.mask_ip(text)
        
        total = sum(counts.values())
        return text, {'total': total, **counts}


# 全局单例
_privacy_mask = None


def get_privacy_mask() -> PrivacyMask:
    """获取隐私脱敏器"""
    global _privacy_mask
    if _privacy_mask is None:
        _privacy_mask = PrivacyMask()
    return _privacy_mask
