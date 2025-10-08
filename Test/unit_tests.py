from classes.objects import *


def runSingletonTest():
    print("===== Testing Singleton Pattern =====")

    # Create a Singleton instance
    singletonPatient_instance = SingletonPatient.get_instance()
    patient = singletonPatient_instance.patient

    print("Updating Singleton fields")
    # Update the fields of the Singleton
    patient.name = "Test"
    patient.age = 30
    patient.CT = "CT"
    patient.fluroscopy = "Fluoro"

    # Check if the fields are updated
    assert patient.name == "Test"
    assert patient.age == 30
    assert patient.CT == "CT"
    assert patient.fluroscopy == "Fluoro"


    # Create another instance of Singleton
    singletonPatient_instance2 = SingletonPatient.get_instance()

    print("Checking if instances are the same")
    # All good if the two instances share the same ID
    assert id(singletonPatient_instance) == id(singletonPatient_instance2)
    
    print("===== Singleton tests passed =====")


def runStateTest():
    print("===== Testing State Pattern =====")
    # Create a Singleton instance
    singleton_instance = SingletonPatient.get_instance()
    # Create the context that will hold the singleton
    context = Context(SegmentState(), singleton_instance)
    # Check to see the state transitions

    # State changes after every process() call
    context.request_process()
    # Check if the state match after every transition
    assert isinstance(context._singleton_data._state, CalibrationState)

    context.request_process()
    assert isinstance(context._singleton_data._state, RegistrationState)

    context.request_process()
    assert isinstance(context._singleton_data._state, ReferenceSysState)

    context.request_process()
    assert isinstance(context._singleton_data._state, MotionState)

    context.request_process()
    assert isinstance(context._singleton_data._state, VisualState)
    print("===== State tests passed =====")


def runFactoryTest():
    print("===== Testing Factory Pattern =====")
    # Create a Singleton instance
    singleton_instance = SingletonPatient.get_instance()
    # Create the context that will hold the singleton
    context = Context(SegmentState(), singleton_instance)
    # State changes after every process() call
    context.request_process()
    # Get string representation of the current state
    currentState = context.request_string()

    # Build the state obj from its string respresentation
    state = StateFactory.get_state(currentState)
    # Check if the state match
    assert isinstance(state, CalibrationState)

    context.request_process()
    currentState = context.request_string()
    state = StateFactory.get_state(currentState)
    assert isinstance(state, RegistrationState)

    context.request_process()
    currentState = context.request_string()
    state = StateFactory.get_state(currentState)
    assert isinstance(state, ReferenceSysState)

    context.request_process()
    currentState = context.request_string()
    state = StateFactory.get_state(currentState)
    assert isinstance(state, MotionState)

    context.request_process()
    currentState = context.request_string()
    state = StateFactory.get_state(currentState)
    assert isinstance(state, VisualState)

    print("===== Factory tests passed =====")

if __name__ == "__main__":

    runSingletonTest()
    print("\n")
    runStateTest()
    print("\n")
    runFactoryTest()




