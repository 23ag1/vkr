"""Tests for mentor message sources (vkr-5m7)."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import BASE_ENV


def _make_chunk(doc_id=None, content="test chunk"):
    c = MagicMock()
    c.document_id = doc_id or uuid.uuid4()
    c.content = content
    return c


def _make_doc(doc_id=None, title="Security Policy"):
    d = MagicMock()
    d.id = doc_id or uuid.uuid4()
    d.title = title
    return d


@pytest.mark.anyio
async def test_sources_include_document_title():
    """Assistant message sources must include document title, not just chunk_ids."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.mentor as svc

        db = AsyncMock()
        session = MagicMock()
        session.id = uuid.uuid4()
        session.user_id = uuid.uuid4()

        doc_id = uuid.uuid4()
        chunk = _make_chunk(doc_id=doc_id, content="RAG content about phishing")
        doc = _make_doc(doc_id=doc_id, title="Phishing Awareness Guide")

        # DB calls: get_session, user_msg commit, list_messages result, document titles
        result_session = MagicMock()
        result_session.scalar_one_or_none.return_value = session

        result_history = MagicMock()
        result_history.scalars.return_value.all.return_value = []

        result_docs = MagicMock()
        result_docs.scalars.return_value.all.return_value = [doc]

        db.execute = AsyncMock(side_effect=[result_session, result_history, result_docs])

        with (
            patch("app.services.rag.retrieve_chunks", AsyncMock(return_value=[chunk])),
            patch("app.services.llm.chat_completion", AsyncMock(return_value="reply text")),
        ):
            msg = await svc.send_message(db, session.id, session.user_id, "How to spot phishing?")

        sources = msg.sources
        assert sources is not None
        assert isinstance(sources, dict)
        docs_list = sources.get("documents")
        assert docs_list is not None
        assert len(docs_list) == 1
        assert docs_list[0]["title"] == "Phishing Awareness Guide"
        assert docs_list[0]["id"] == str(doc_id)


@pytest.mark.anyio
async def test_sources_deduplicated_by_document():
    """Two chunks from same document → one source entry."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.mentor as svc

        db = AsyncMock()
        session = MagicMock()
        session.id = uuid.uuid4()
        session.user_id = uuid.uuid4()

        doc_id = uuid.uuid4()
        chunk1 = _make_chunk(doc_id=doc_id, content="chunk 1")
        chunk2 = _make_chunk(doc_id=doc_id, content="chunk 2")
        doc = _make_doc(doc_id=doc_id, title="Main Document")

        result_session = MagicMock()
        result_session.scalar_one_or_none.return_value = session
        result_history = MagicMock()
        result_history.scalars.return_value.all.return_value = []
        result_docs = MagicMock()
        result_docs.scalars.return_value.all.return_value = [doc]

        db.execute = AsyncMock(side_effect=[result_session, result_history, result_docs])

        with (
            patch("app.services.rag.retrieve_chunks", AsyncMock(return_value=[chunk1, chunk2])),
            patch("app.services.llm.chat_completion", AsyncMock(return_value="reply")),
        ):
            msg = await svc.send_message(db, session.id, session.user_id, "question")

        docs_list = msg.sources["documents"]
        assert len(docs_list) == 1
