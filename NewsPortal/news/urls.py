from django.urls import path
from django.views.decorators.cache import cache_page

from .views import (
   PostList,
   PostDetail,
   SearchPostList,
   PostCreate,
   PostDelete,
   PostUpdate,
   CategoryList,
   subscribe,
   TestCeleryView,
)

urlpatterns = [
   path('testcelery/', TestCeleryView.as_view()),

   path('news/', cache_page(60)(PostList.as_view()), name = 'post_list'),
   path('news/<int:pk>', cache_page(60*5)(PostDetail.as_view()), name='post_detail'),
   path('news/search/', SearchPostList.as_view(), name='news_search'), # GET queries are possible

   path('news/create/',          PostCreate.as_view(), name='news_create'),
   path('news/<int:pk>/delete/', PostDelete.as_view(), name='news_delete'),
   path('news/<int:pk>/edit/',   PostUpdate.as_view(), name='news_edit'),

   path('article/create/',          PostCreate.as_view(), name='article_create'),
   path('article/<int:pk>/delete/', PostDelete.as_view(), name='article_delete'),
   path('article/<int:pk>/edit/',   PostUpdate.as_view(), name='article_edit'),

   path('categories/<int:pk>', CategoryList.as_view(), name='category_list'),
   path('categories/<int:pk>/subscribers', subscribe,  name='subscribe'),
]
