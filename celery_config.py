from flaskr import create_app, make_celery

app = create_app('default')
celery = make_celery(app)

if __name__ == '__main__':
    celery.start()
