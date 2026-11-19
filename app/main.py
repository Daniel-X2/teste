import logging
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from .config import CRON_EXPRESSION
from .database import SessionLocal, get_db
from .models import Cliente, Funcionario, Produto

logger = logging.getLogger("api")

scheduler = BackgroundScheduler()

# Histórico fica em memória: o job é somente leitura, não grava no banco.
historico: deque[dict] = deque(maxlen=50)
historico_lock = Lock()


def coletar_resumo(db: Session) -> dict:
    """Faz os SELECTs do resumo. Não altera nenhuma linha."""
    total_estoque = db.scalar(
        select(func.coalesce(func.sum(Produto.quantidade * Produto.valor_revenda), 0))
    ) or 0

    return {
        "clientes": db.scalar(select(func.count()).select_from(Cliente)) or 0,
        "funcionarios": db.scalar(select(func.count()).select_from(Funcionario)) or 0,
        "produtos": db.scalar(select(func.count()).select_from(Produto)) or 0,
        "valor_total_estoque": float(total_estoque),
    }


def registrar_execucao() -> dict:
    """Tarefa agendada: lê o banco e guarda o snapshot no histórico em memória."""
    with SessionLocal() as db:
        resumo = coletar_resumo(db)

    execucao = {
        "executado_em": datetime.now(timezone.utc).isoformat(),
        **resumo,
    }
    with historico_lock:
        historico.appendleft(execucao)
    return execucao


def ultima_execucao() -> dict | None:
    with historico_lock:
        return historico[0] if historico else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Não criamos tabelas: cliente/funcionario/produto já existem no Supabase.
    try:
        registrar_execucao()
    except Exception:
        logger.exception("Falha na primeira leitura do banco na inicialização")

    if not scheduler.running:
        scheduler.add_job(
            registrar_execucao,
            CronTrigger.from_crontab(CRON_EXPRESSION),
            id="leitura_horaria",
            name="Leitura horária do banco",
            replace_existing=True,
        )
        scheduler.start()

    yield

    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="API de leitura horária do banco",
    description="Job agenda SELECTs no Supabase de hora em hora e expõe resumo e listagens.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def raiz():
    return {
        "mensagem": "API online.",
        "rotas": ["/health", "/resumo", "/clientes", "/funcionarios", "/produtos"],
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Banco indisponível: {exc}") from exc

    return {
        "status": "ok",
        "banco": "conectado",
        "job_agendado": scheduler.running,
        "cron": CRON_EXPRESSION,
    }


@app.get("/resumo")
def resumo(db: Session = Depends(get_db)):
    """Métricas ao vivo + snapshot da última execução do job."""
    return {
        "agora": coletar_resumo(db),
        "ultima_execucao": ultima_execucao(),
    }


@app.get("/job/execucoes")
def listar_execucoes():
    with historico_lock:
        return list(historico)


@app.post("/job/executar", status_code=201)
def executar_agora():
    """Dispara a leitura na hora, sem esperar o cron."""
    try:
        return registrar_execucao()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Falha ao ler o banco: {exc}") from exc


@app.get("/clientes")
def listar_clientes(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    registros = db.scalars(select(Cliente).order_by(Cliente.id).limit(limit).offset(offset)).all()
    return [registro.as_dict() for registro in registros]


@app.get("/funcionarios")
def listar_funcionarios(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    registros = db.scalars(
        select(Funcionario).order_by(Funcionario.id).limit(limit).offset(offset)
    ).all()
    return [registro.as_dict() for registro in registros]


@app.get("/produtos")
def listar_produtos(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    registros = db.scalars(select(Produto).order_by(Produto.id).limit(limit).offset(offset)).all()
    return [registro.as_dict() for registro in registros]
