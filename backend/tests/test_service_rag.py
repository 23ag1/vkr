import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import BASE_ENV


def _mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.mark.anyio
async def test_chunk_text_splits_by_size():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.rag as svc
        reload(svc)

        text = "word " * 300
        chunks = svc.chunk_text(text, max_tokens=100, overlap=20)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.split()) <= 120


@pytest.mark.anyio
async def test_chunk_text_short_returns_single():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.rag as svc
        reload(svc)

        text = "Short text."
        chunks = svc.chunk_text(text, max_tokens=500, overlap=50)
        assert len(chunks) == 1
        assert chunks[0] == text


@pytest.mark.anyio
async def test_embed_text_calls_openai():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.rag as svc
        import app.services.llm as llm_svc
        reload(llm_svc)
        reload(svc)

        mock_resp = MagicMock()
        mock_resp.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_resp)

        with patch.object(llm_svc, "_client", mock_client):
            result = await svc.embed_text("test text")

        assert len(result) == 1536
        assert result[0] == pytest.approx(0.1)


@pytest.mark.anyio
async def test_ingest_document_creates_chunks():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.rag as svc
        reload(svc)

        db = _mock_db()
        db.refresh = AsyncMock(side_effect=lambda x: None)
        mock_embeddings = [[0.0] * 1536, [0.0] * 1536]

        with patch.object(svc, "_embed_batch", AsyncMock(return_value=mock_embeddings)):
            await svc.ingest_document(db, title="Test Doc", content="word " * 20, source="upload")

        assert db.add.call_count >= 2


@pytest.mark.anyio
async def test_retrieve_chunks_returns_list():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.rag as svc
        reload(svc)

        chunk = MagicMock()
        chunk.content = "Phishing content"
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [chunk]
        db = _mock_db()
        db.execute.return_value = mock_result

        with patch.object(svc, "embed_text", AsyncMock(return_value=[0.1] * 1536)):
            results = await svc.retrieve_chunks(db, query="phishing", top_k=5)

        assert results == [chunk]
