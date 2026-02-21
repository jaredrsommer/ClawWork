"""
Revenue Stream Registry

All 10 revenue streams, importable by STREAM_ID.
"""

from . import ghostwriting
from . import products
from . import seo_content
from . import slide_decks
from . import research
from . import podcast
from . import publishing
from . import data_analysis
from . import newsletter
from . import saas_api

REGISTRY = {
    ghostwriting.STREAM_ID: ghostwriting,
    products.STREAM_ID: products,
    seo_content.STREAM_ID: seo_content,
    slide_decks.STREAM_ID: slide_decks,
    research.STREAM_ID: research,
    podcast.STREAM_ID: podcast,
    publishing.STREAM_ID: publishing,
    data_analysis.STREAM_ID: data_analysis,
    newsletter.STREAM_ID: newsletter,
    saas_api.STREAM_ID: saas_api,
}
