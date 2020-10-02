import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  questions_page = questions[start:end]

  return questions_page

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)

  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app, resources={r"/api/*": {"origins": "*"}})

  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  # CORS Headers
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


  '''
  @TODO:
  Create an endpoint to handle GET requests
  for all available categories.
  '''
  @app.route('/categories')
  def retrieve_categories():
    categories = Category.query.order_by(Category.id).all()
    formatted_categories = {category.id: category.type for category in categories}

    if len(formatted_categories) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'categories': formatted_categories,
      'total_categories': len(Category.query.all())
    })

  '''
  @TODO:
  Create an endpoint to handle GET requests for questions,
  including pagination (every 10 questions).
  This endpoint should return a list of questions,
  number of total questions, current category, categories.

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions.
  '''

  @app.route('/questions')
  def retrieve_questions():
    selection = Question.query.order_by(Question.id).all()
    questions_page = paginate_questions(request, selection)

    categories = Category.query.order_by(Category.id).all()
    formatted_categories = {category.id: category.type for category in categories}

    if len(questions_page) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'questions': questions_page,
      'total_questions': len(Question.query.all()),
      'categories': formatted_categories,
      'current_category': None
    })

  # Test
  # curl localhost:5000/questions
  # curl localhost:5000/questions?page=1

  '''
  @TODO:
  Create an endpoint to DELETE question using a question ID.

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page.
  '''

  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()

      if question is None:
        abort(404)

      question.delete()

      categories = Category.query.order_by(Category.id).all()
      formatted_categories = {category.id: category.type for category in categories}
      selection = Question.query.order_by(Question.id).all()
      questions_page = paginate_questions(request, selection)

      return jsonify({
        'success': True,
        'deleted': question_id,
        'questions': questions_page,
        'total_questions': len(Question.query.all()),
        'current_category': None,
        'categories': formatted_categories
      })

    except:
      abort(422)


  '''
  @TODO:
  Create an endpoint to POST a new question,
  which will require the question and answer text,
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab,
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.
  '''

  @app.route('/questions', methods=['POST'])
  def create_new_question():
    body = request.get_json()

    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_category = body.get('category', None)
    new_difficulty = body.get('difficulty', None)
    search = body.get('searchTerm', None)

    try:
      if search:
        selection = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(search)))
        questions_page = paginate_questions(request, selection)

        return jsonify({
          'success': True,
          'questions': questions_page,
          'total_questions': selection.count(),
          'current_category': None
        })

      else:
        question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
        question.insert()

        categories = Category.query.order_by(Category.id).all()
        formatted_categories = {category.id: category.type for category in categories}
        selection = Question.query.order_by(Question.id).all()
        questions_page = paginate_questions(request, selection)

        return jsonify({
          'success': True,
          'created': question.id,
          'questions': questions_page,
          'total_questions': len(Question.query.all()),
          'categories': formatted_categories
        })

    except:
      abort(422)

    # Test
    #

  '''
  @TODO:
  Create a POST endpoint to get questions based on a search term.
  It should return any questions for whom the search term
  is a substring of the question.

  TEST: Search by any phrase. The questions list will update to include
  only question that include that string within their question.
  Try using the word "title" to start.
  '''

  # See above for modified /questions POST route

  '''
  @TODO:
  Create a GET endpoint to get questions based on category.

  TEST: In the "List" tab / main screen, clicking on one of the
  categories in the left column will cause only questions of that
  category to be shown.
  '''

  @app.route('/categories/<int:category_id>/questions')
  def retrieve_questions_by_category(category_id):
    try:
      selection = Question.query.order_by(Question.id).filter(Question.category == category_id).all()
      questions_page = paginate_questions(request, selection)
      current_category = Category.query.filter(Category.id == category_id).first().type

      return jsonify({
        'success': True,
        'questions': questions_page,
        'total_questions': len(selection),
        'current_category': current_category
      })

    except:
      abort(422)

  '''
  @TODO:
  Create a POST endpoint to get questions to play the quiz.
  This endpoint should take category and previous question parameters
  and return a random question within the given category,
  if provided, and that is not one of the previous questions.

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not.
  '''

  @app.route('/quizzes', methods=['POST'])
  def play_quiz():
    body = request.get_json()
    previous_questions = body.get('previous_questions', [])
    quiz_category = body.get('quiz_category', None)

    try:
      if quiz_category:
        quiz_questions = Question.query.filter(Question.category == quiz_category['id']).filter(Question.id.notin_(previous_questions)).all()
      else:
        quiz_questions = Question.query.filter(Question.id.notin_(previous_questions)).all()

      current_question = random.choice(quiz_questions)
      current_question_formatted = current_question.format()

      previous_questions.append(current_question_formatted['id'])

      return jsonify({
        'success': True,
        'previous_questions': previous_questions,
        'current_question': current_question_formatted
      })

    except:
      abort(422)

  # Test
  # curl -X POST -H "Content-Type: application/json" -d '{}' localhost:5000/quizzes
  # curl -X POST -H "Content-Type: application/json" -d '{"previous_questions": [20,22], "quiz_category": {"type": "Science", "id": "1"}}' localhost:5000/quizzes

  '''
  @TODO:
  Create error handlers for all expected errors
  including 404 and 422.
  '''

  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
        'success': False,
        'error': 400,
        'message': 'bad request'
      }), 400

  @app.errorhandler(404)
  def not_found(error):
      return jsonify({
        'success': False,
        'error': 404,
        'message': 'resource not found'
      }), 404

  @app.errorhandler(405)
  def not_found(error):
      return jsonify({
        'success': False,
        'error': 405,
        'message': 'method not allowed'
      }), 405

  @app.errorhandler(422)
  def unprocessable(error):
      return jsonify({
        'success': False,
        'error': 422,
        'message': 'unprocessable'
      }), 422

  @app.errorhandler(500)
  def internal_server_error(error):
      return jsonify({
        'success': False,
        'error': 500,
        'message': 'internal server error'
      }), 500

  return app
