import timestamp


class Logging:

    def log_command(self, user, command: str):
        print(f"{timestamp.timestamp()} '{user}' used command {command.upper()}")

    def log_error(self, error, command: str):
        print(f"{timestamp.timestamp()} {command.upper()} command caught an exception: {repr(error)}")