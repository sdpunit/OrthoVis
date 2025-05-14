from __future__ import annotations
from abc import ABC, abstractmethod
from objects import Patient
from singleton import SingletonPatient


class Context:
    """
    The Context defines the interface of interest to clients. It also maintains
    a reference to an instance of a State subclass, which represents the current
    state of the Context.
    """

    _state = None
    _singleton_patient = None
    # _name = None
    # _description = None
    """
    A reference to the current state of the Context.
    """

    def __init__(self, state: ProjectState, patient:SingletonPatient) -> None:
        self.transition_to(state)
        self._singleton_patient = patient
        # self._name = patient.name
        # self._description = description

    def transition_to(self, state: ProjectState):
        """
        The Context allows changing the State object at runtime.
        """

        print(f"Context: Transition to {type(state).__name__}")
        self._state = state
        self._state.context = self

    """
    The Context delegates part of its behavior to the current State object.
    """

    def request(self):
        self._state.handle()



class ProjectState(ABC):
    """
    The base State class declares methods that all Concrete State should
    implement and also provides a backreference to the Context object,
    associated with the State. This backreference can be used by States to
    transition the Context to another State.
    """

    @property
    def context(self) -> Context:
        return self._context

    @context.setter
    def context(self, context: Context) -> None:
        self._context = context

    @abstractmethod
    def handle(self) -> None:
        pass



"""
Concrete States implement various behaviors, associated with a state of the
Context.
"""

class HomePageState(ProjectState):
    def handle(self) -> None:
        print("HomePageState wants to change the state of the context.")
        self.context.transition_to(SegmentState())

class SegmentState(ProjectState):
    def handle(self) -> None:
        print("SegmentState wants to change the state of the context.")
        self.context.transition_to(CalibrationState())

class CalibrationState(ProjectState):
    def handle(self) -> None:
        print("CalibrationState wants to change the state of the context.")
        self.context.transition_to(RegistrationState())

class RegistrationState(ProjectState):
    def handle(self) -> None:
        print("Registration wants to change the state of the context.")
        self.context.transition_to(ReferenceSysState())

class ReferenceSysState(ProjectState):
    def handle(self) -> None:
        print("ReferenceSysState wants to change the state of the context.")
        self.context.transition_to(MotionState())

class MotionState(ProjectState):
    def handle(self) -> None:
        print("Motion wants to change the state of the context.")
        self.context.transition_to(VisualState())

class VisualState(ProjectState):
    def handle(self) -> None:
        self.context.transition_to(None)


#if __name__ == "__main__":
#     # The client code.
#     singletonPatient_instance = SingletonPatient.get_instance()
#     context = Context(HomePageState())
#     context.request()
#     context.request()
#     context.request()
#     context.request()