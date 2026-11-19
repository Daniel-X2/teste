from sqlalchemy import Boolean, Column, Integer, Numeric, String, Text

from .database import Base


class Cliente(Base):
    __tablename__ = "cliente"

    id = Column(Integer, primary_key=True)
    nome = Column(String(30))
    cpf = Column(Text)
    conta = Column(Integer)
    isvip = Column(Boolean)
    data = Column(Integer)
    empresa = Column(String(255))

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "cpf": self.cpf,
            "conta": self.conta,
            "isvip": self.isvip,
            "data": self.data,
            "empresa": self.empresa,
        }


class Funcionario(Base):
    __tablename__ = "funcionario"

    id = Column(Integer, primary_key=True)
    nome = Column(String(30))
    cpf = Column(Text)
    senha_hash = Column(Text)  # nunca exposta pela API
    isadmin = Column(Boolean)
    quantidade_atestado = Column(Integer)
    nascimento = Column(Integer)
    data = Column(Integer)

    def as_dict(self) -> dict:
        # senha_hash deliberadamente omitido
        return {
            "id": self.id,
            "nome": self.nome,
            "cpf": self.cpf,
            "isadmin": self.isadmin,
            "quantidade_atestado": self.quantidade_atestado,
            "nascimento": self.nascimento,
            "data": self.data,
        }


class Produto(Base):
    __tablename__ = "produto"

    id = Column(Integer, primary_key=True)
    nome = Column(String(30))
    codigo = Column(Integer)
    quantidade = Column(Integer)
    valor_revenda = Column(Numeric)
    lote = Column(Integer)

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "codigo": self.codigo,
            "quantidade": self.quantidade,
            "valor_revenda": float(self.valor_revenda) if self.valor_revenda is not None else None,
            "lote": self.lote,
        }
