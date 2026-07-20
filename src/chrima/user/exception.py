class UserNotFoundException(Exception):
    def __init__(self):
        super().__init__("User not found.")


class UserValidationException(Exception):
    pass


class IncorrectPasswordException(Exception):
    def __init__(self):
        super().__init__("Incorrect password.")
