# scripts package
# 合同审查辅助系统 - 核心模块包

__version__ = '1.0.0'

# 导出主要类
from .contract_review import ContractReviewer, RiskLevel, Clause, ReviewResult
from .word_generator import WordGenerator
from .email_sender import EmailSender, create_email_template

__all__ = [
    'ContractReviewer',
    'RiskLevel', 
    'Clause',
    'ReviewResult',
    'WordGenerator',
    'EmailSender',
    'create_email_template'
]
