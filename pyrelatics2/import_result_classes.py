import dataclasses
import datetime
import typing

from colorama import Fore, Style

# Type aliases
ImportMessageStatus = typing.Literal["Progress", "Comment", "Success", "Warning", "Error"]
ImportElementActions = typing.Literal["Add", "Update"]


@dataclasses.dataclass(kw_only=True)
class ImportMessage:
    """
    Data class for a message in the result of an import
    """

    time: datetime.time
    status: ImportMessageStatus
    message: str
    row: int

    status_fore_color = {
        "Progress": Fore.BLUE,
        "Comment": Fore.RESET,
        "Success": Fore.GREEN,
        "Warning": Fore.YELLOW,
        "Error": Fore.RED,
    }

    def __post_init__(self):
        """
        Convert a date given as string into a date
        """
        self.time = datetime.time.fromisoformat(self.time)

    def __str__(self) -> str:
        status_color = self.status_fore_color[self.status]
        return f"{self.time}  {self.row:05}  {status_color}{self.status:<8}{Fore.RESET}  {self.message}"


@dataclasses.dataclass(kw_only=True)
class ImportElement:
    """
    Data class for a changed element in the result of an import
    """

    action: ImportElementActions
    id: str  # pylint: disable=invalid-name
    foreign_key: str

    def __str__(self) -> str:
        return f"{self.action:<6}  {self.id}  {self.foreign_key}"


@dataclasses.dataclass(kw_only=True)
class ImportResult:
    """
    Data class containing the result of an import
    """

    messages: list[ImportMessage] = dataclasses.field(default_factory=list)
    elements: list[ImportElement] = dataclasses.field(default_factory=list)
    total_rows: int = dataclasses.field(init=False)
    elapsed_time: datetime.timedelta = dataclasses.field(init=False)

    @staticmethod
    def from_suds(suds_response) -> "ImportResult":  # "", see https://peps.python.org/pep-0484/#forward-references
        """
        Parse the raw suds response <sudsobject> for messages and elements and respond with a filled ImportResult object

        Args:
            suds_response : Raw <sudsobject> response from the import request
        """
        result = ImportResult()

        # TODO: Check if .Import. exists and handle appropriately

        # Add all the messages when available
        if suds_response.Import.Message:
            row = 0

            for msg in suds_response.Import.Message:
                # Monitor any row changes
                if msg._Result == "Progress":  # pylint: disable=W0212
                    if "Processing row :" in msg.value:
                        row = int(msg.value[17:])

                    if "Total rows imported:" in msg.value:
                        result.total_rows = int(msg.value[21:])

                    if "Total time (ms):" in msg.value:
                        result.elapsed_time = datetime.timedelta(milliseconds=int(msg.value[17:]))

                result.messages.append(
                    ImportMessage(
                        time=msg._Time, status=msg._Result, message=msg.value, row=row  # pylint: disable=W0212
                    )
                )

        # Add all the elements when available
        if suds_response.Import.Elements and suds_response.Import.Elements[0]:
            for elem in suds_response.Import.Elements[0]:
                result.elements.append(
                    ImportElement(
                        action=elem._Action, id=elem._ID, foreign_key=elem._ForeignKey  # pylint: disable=W0212
                    )
                )

        return result

    def __str__(self) -> str:
        result = ""
        result += f"Rows imported : {self.total_rows}\n"
        result += f"Elapsed time  : {self.elapsed_time} (h:mm:ss.mmmmmm)\n"
        result += "[Messages]: \n"
        result += Style.BRIGHT + "Time      Row    Status    Message\n" + Style.RESET_ALL
        for msg in self.messages:
            result += f"{msg.__str__()} \n"
        result += "[Elements]: \n"
        result += Style.BRIGHT + "Action  ID                                    Foreign key\n" + Style.RESET_ALL
        for elem in self.elements:
            result += f"{elem.__str__()} \n"

        return result

    def filter_messages(self, status: ImportMessageStatus) -> list[ImportMessage]:
        """
        Return the list of messages with the given status

        Returns:
            list[ImportMessage]: List of messages
        """
        return [_ for _ in self.messages if _.status == status]

    # ["Progress", "Comment", "Success", "Warning", "Error"]
    @property
    def progress_messages(self) -> list[ImportElement]:
        """Get a list of all the progress messages"""
        return self.filter_messages("Progress")

    @property
    def comment_messages(self) -> list[ImportElement]:
        """Get a list of all the comment messages"""
        return self.filter_messages("Comment")

    @property
    def success_messages(self) -> list[ImportElement]:
        """Get a list of all the comment messages"""
        return self.filter_messages("Success")

    @property
    def warning_messages(self) -> list[ImportElement]:
        """Get a list of all the comment messages"""
        return self.filter_messages("Warning")

    @property
    def error_messages(self) -> list[ImportElement]:
        """Get a list of all the comment messages"""
        return self.filter_messages("Error")

    def filter_elements(self, action: ImportElementActions) -> list[ImportMessage]:
        """
        Return the list of elements with the given action

        Returns:
            list[ImportMessage]: List of messages
        """
        return [_ for _ in self.elements if _.action == action]

    # ["Add", "Update"]
    @property
    def added_elements(self) -> list[ImportElement]:
        """Get a list of all the added elements"""
        return self.filter_elements("Add")

    @property
    def updated_elements(self) -> list[ImportElement]:
        """Get a list of all the updated elements"""
        return self.filter_elements("Update")
