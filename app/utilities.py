from app import mongo
from .crypto import generate_keys

from activipy import vocab
from flask import request, abort, url_for
from flask_login import current_user
import datetime, json


def return_new_user(handle, displayName, email, passwordHash):
  public, private = generate_keys()

  user =   {  
            'id': 'acct:'+handle+'@'+request.host, 
            '@context': [
                          'https://www.w3.org/ns/activitystreams',
                          {'manuallyApprovesFollowers': 'as:manuallyApprovesFollowers'}
                        ],
            'type': 'Person', 
            'username': handle,
            'acct': handle+'@'+request.host,
            'url': request.url_root+'users/'+handle,
            'name': displayName, 
            'email': email, 
            'password': passwordHash,
            'manuallyApprovesFollowers': False,
            'avatar': url_for('static', filename='img/defaultAvatar.png'),
            'header': url_for('static', filename='img/defaultHeader.gif'),
            'following': request.url_root+'api/'+handle+'/following', 
            'followers': request.url_root+'api/'+handle+'/followers', 
            'liked': request.url_root+'api/'+handle+'/liked', 
            'inbox': request.url_root+'api/'+handle+'/inbox', 
            'outbox': request.url_root+'api/'+handle+'/feed',
            'metrics': {'post_count': 0},
            'created_at': get_time(),
            'publicKey': {
                          'id': request.url_root+'users/'+handle+'#main-key',
                          'owner': request.url_root+'users/'+handle,
                          'publicKeyPem': public
                          },
            'privateKey': private
          }


  return user
def find_user_or_404(handle):
  u = mongo.db.users.find_one({'username': handle})
  if not u:
    abort(404)
  else:
    return u
def get_logged_in_user():
  u = mongo.db.users.find_one({'id': current_user.get_id()})
  if not u:
    abort(404)
  else:
    return u


def get_time():

  return datetime.datetime.now().isoformat()
def createPost(content, handle, to, cc):
  u = find_user_or_404(handle)
  
  post_number = str(u['metrics']['post_count'])
  id = request.url_root+u['username']+'/posts/'+post_number
  note_url = request.url_root+'@'+post_number
  
  time = get_time()

  create =  {
            'id': id+'/activity',
            'type': 'Create',
            'context': vocab.Create().types_expanded,
            'actor': u['acct'],
            'published': time,
            'to': to,
            'cc': cc,
            'object': {
                        'id': id,
                        'type': 'Note',
                        'summary': None,
                        'content': content,
                        'published': time,
                        'url': note_url,
                        'attributedTo': u['acct'],
                        'to': to,
                        'cc': cc
                      }
          }
  return json.dumps(create)
def createLike(actorAcct, post):
  to = post['attributedTo']
  if to in post:
    for t in post['to']:
      to.append(t)
  return vocab.Like(
                    context="https://www.w3.org/ns/activitystreams",
                    actor=actorAcct,
                    to=to,
                    object=vocab.Note(
                                      context={"@language": 'en'},
                                      id=post['@id'],
                                      attributedTo=post['attributedTo'],
                                      content=post['content']))

def follow_user(actorAcct, otherUser):
  return vocab.Follow(
                      context="https://www.w3.org/ns/activitystreams",
                      actor=actorAcct,
                      object=vocab.User(
                                        context={"@language": 'en'},
                                        id=otherUser['id']))

def accept_follow(actorAcct, followActivity):
  return vocab.Accept(
                      context="https://www.w3.org/ns/activitystreams",
                      actor=actorAcct,
                      object=followActivity)


# API
def check_accept_headers(request):
  if request.headers.get('accept'):
    if (request.headers['accept'] == 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"') or (request.headers['accept'] == 'application/activity+json'):
      return True
  return False

def check_content_headers(request):
  if request.headers.get('Content-Type'):
    if (request.headers['Content-Type'] == 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"') or (request.headers['Content-Type'] == 'application/activity+json'):
      return True
  return False
