from django.shortcuts import render
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt

from mywebsite.models import Post

from django.http import JsonResponse
import json

def homepage(request):
    now = datetime.now()
    students = ['Alice', 'Bob', 'Charlie', 'Diana']
    return render(request, "index.html", locals())

def get_db_result(request):
    posts = Post.objects.all()
    return render(request, "index_get_db_result.html", locals())

@csrf_exempt
def api(request):
    if request.method == 'GET':
        keyword = request.GET.get('keyword')
        limit = request.GET.get('limit') 
        
        # Check the values before using them
        if keyword and limit:
            print(keyword + ' ' + limit)

        # Retrieve the latest posts from the database
        posts = Post.objects.all()
        post_list = []

        for post in posts:
            post_list.append({
                'title': post.title,
                'body': post.body,
                'pub_date': post.pub_date.strftime('%Y-%m-%d %H:%M:%S')
            })
        # Return the list of posts as JSON
        return JsonResponse({'posts': post_list})

    elif request.method == 'POST':
        try:
            if not request.body:
                return JsonResponse({'error': 'Empty body'}, status=400)
            
            # Parse the JSON data from the request body
            data = json.loads(request.body.decode('utf-8'))
            title = data.get('title')
            body = data.get('body')

            if title and body:
                # Create a new Post object and save it to the database
                post = Post.objects.create(title=title, body=body)

                # Return the created post's information
                return JsonResponse({
                    'message': 'Post created successfully',
                    'post': {
                        'id': post.id,
                        'title': post.title,
                        'body': post.body,
                        'pub_date': post.pub_date.strftime('%Y-%m-%d %H:%M:%S')
                    }
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    else:
        # Method not allowed
        return JsonResponse({'error': 'Only GET and POST methods are supported'}, status=405)