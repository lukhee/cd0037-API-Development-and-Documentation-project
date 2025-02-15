import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, result):
    print("result")
    print(request)
    print("result")
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in result]
    current_questions = questions[start:end]
    return current_questions



def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app)

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Headers', 'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route("/categories", methods=["GET"])
    def get_categories():
        category_result = Category.query.order_by(Category.id).all()
        # Format Result
        categories = [category.format() for category in category_result]

        return jsonify(
            {
                "success": True,
                "categories": categories,
            }
        )


    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    @app.route("/questions")
    def get_questions():
        # Setting the categorie
        category_result = Category.query.order_by(Category.id).all()
        # Setting the Questions
        result = Question.query.order_by(Question.id).all()
        current_question = paginate_questions(request, result)
        if len(current_question) == 0:
            abort(404)

        # Format Categories
        categories = [category.format() for category in category_result]

        return jsonify(
            {
                "success": True,
                "categories": categories,
                "questions": current_question,
                "total_questions": len(result)
            }
        )

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()
            if question is None:
                abort(404)

            question.delete()
            result = Question.query.order_by(Question.id).all()
            current_question = paginate_questions(request, result)

            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                    "questions": current_question,
                    "total_questions": len(result),
                }
            )

        except:
            abort(422)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """

    @app.route("/questions", methods=["POST"])
    def create_question():
        body = request.get_json()

        question = body.get("question", None)
        answer = body.get("answer", None)
        category = body.get("category", None)
        difficulty = body.get("difficulty", None)

        try:
            question = Question(question=question, answer=answer, category=category, difficulty=difficulty)
            question.insert()

            result = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, result)

            return jsonify(
                {
                    "success": True,
                    "created": question.id,
                    "questions": current_questions,
                    "total_questions": len(result),
                }
            )

        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    @app.route("/questions/search", methods=["POST"])
    def search_question():
        body = request.get_json()
        searchTerm = body.get("searchTerm", None)

        try:
            result = Question.query.filter(Question.question.ilike('%'+searchTerm+'%')).all()

            current_questions = paginate_questions(request, result)

            return jsonify(
                {
                    "success": True,
                    "questions": current_questions,
                    "total_questions": len(result),
                }
            )

        except:
            abort(422)

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route("/categories/<int:category_id>/questions")
    def get_questions_by_category(category_id):
        result = Question.query.filter(Question.category==category_id).all()
        # Setting the Questions
        current_question = paginate_questions(request, result)
        if len(current_question) == 0:
            abort(404)

        # Format Categories
        print(current_question)
        # categories = [category.format() for category in current_question]

        return jsonify(
            {
                "success": True,
                "questions": current_question,
                "current_category": category_id,
                "total_questions": len(result)
            }
        )

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route("/quizzes", methods=["POST"])
    def get_quizzes():
        result = []
        body = request.get_json()
        previous_questions = body.get("previous_questions", None)
        quiz_category = body.get("quiz_category", None)

        # function that filters un-answered questioned
        def fun(variable):
            if (variable['id'] in previous_questions):
                return False
            else:
                return True

        try:
            if quiz_category:
                result = Question.query.filter(Question.category == quiz_category).all()
            else:
                 result = Question.query.order_by(Question.id).all()

            # Format Question into array of object
            questions = [question.format() for question in result]

            # using filter function
            filtered = filter(fun, questions)
            resulted_filtered = []
            for s in filtered:
                resulted_filtered.append(s)
            
            # generate a random number and question
            a=random.randint(0,len(resulted_filtered))
            randomQuestion = resulted_filtered[a]
            print(a)
            

            return jsonify(
                {
                    "success": True,
                    "previous_questions": previous_questions,
                    "currentQuestion": randomQuestion,
                }
            )

        except:
            abort(422)
    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
        "success": False, 
        "error": 422,
        "message": "unprocessable"
        }), 422

    @app.errorhandler(404)
    def unprocessable(error):
        return jsonify({
        "success": False, 
        "error": 404,
        "message": "Not found"
        }), 404

    @app.errorhandler(400)
    def unprocessable(error):
        return jsonify({
        "success": False, 
        "error": 400,
        "message": "Bad request"
        }), 400

    @app.errorhandler(405)
    def unprocessable(error):
        return jsonify({
        "success": False, 
        "error": 405,
        "message": "method not allowed"
        }), 405


    return app

