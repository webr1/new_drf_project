from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .permissions import IsAuthorOrReadOnly
from .models import Category, Post
from .serializers import ( 
    CategorySerializer,
    PostListSerializer,
    PostDetailSerializer,
    PostCreateUpdateSerializer
)



class CategoryListCreateView(generics.ListCreateAPIView):
    """ API ENDPOINTS """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter,filters.OrderingFilter]
    search_fields = ['name','description']
    ordering_fileds = ['name','created_at']
    ordering = ['name']


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

class  PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_fields = ['category','author','status']
    serach_fields = ['title','context']
    ordering_fields = ['created_at','updated_at','views_count','title']
    orderig = ['-created_at']


    def get_queryset(self):
        queryset = Post.objects.select_related('author','category')

        if not self.request.user.is_authenticated:
            queryset =  queryset.filter(status='published')
        else :
            queryset = queryset.filter(Q(status='published') | Q(author = self.request.user))

        return queryset
    

    def get_serializer_class(self):
        if self.request.method == 'POST' :
            return PostCreateUpdateSerializer
        return PostListSerializer
    
class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.select_related('author','category')
    serializer_class = PostDetailSerializer
    permission_classes = [IsAuthorOrReadOnly]
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.request.method == ['PUT','PATCH'] :
            return PostCreateUpdateSerializer
        return PostDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        isinstance = self.get_object()

        if request.method == 'GET':

            isinstance.increments_views()

        serializer = self.get_serializer(isinstance)
        return Response(serializer.data)
    
class MyPostsView(generics.ListAPIView):
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_fields = ['category','status']
    search_fields = ['title','content']
    ordering_fields = ['created_at','updated_at','views_count',]
    ordering = ['-created_at']

    def get_queryset(self):
        return Post.objects.filter(
            author =self.request.user
        ).select_related('author','category')
    

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def popular_post(request):
    posts = Post.objects.filter(status="published").select_related('author','category').order_by('-views_cout')[:10]
    serializer = PostListSerializer(posts,many=True,context = {'request':request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def post_by_category(request,category_slug):
    category = get_object_or_404(Category,slug=category_slug)

    posts =Post.objects.filter(
        status="published",

    ).select_related('author','category').order_by('-created_at')

    serizlizer = PostListSerializer(posts,many=True,cotext='reuquest')

    return Response({
        'category':CategorySerializer(category).data,
        'posts':serizlizer.data
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def recent_posts(request):
    """10 последних опубликованных постов"""
    posts = Post.objects.with_subscription_info().filter(
        status='published'
    ).order_by('-created_at')[:10]
    
    serializer = PostListSerializer(
        posts, 
        many=True, 
        context={'request': request}
    )
    return Response(serializer.data)