from __future__ import annotations

from abc import abstractmethod

from server.LRP import ASTElement, Location


class StateMachine(ASTElement):
    """Represents a state machine.

    Attributes:
        name (str): name of the state machine.
        initial_state (InitialState): initial state of the state machine.
        states (list[State]): list of the states directly contained in the state machine.
    """

    def __init__(self, name: str, location: Location | None = None) -> None:
        super().__init__('stateMachine.stateMachine', location)
        self.name = name
        self.initial_state: InitialState | None = None
        self.states: list[State] = []

    def to_dict(self) -> dict:
        return super().construct_dict(
            {'name': self.name},
            {'states': list(map(lambda state: state.to_dict(), self.states))},
            {'initialState': '' if self.initial_state is None else self.initial_state.target.id, }
        )


class State(ASTElement):
    """Abstract class for a state.

    Attributes:
        name (str): name of the state.
        parent_state (State): composite state containing the current state. For states at the top-level, this attribute is None.
        is_final (bool): True if the state is final, False otherwise.
        outgoing_transitions (list[Transition]): list of transitions going out of the state.
        incoming_transitions (list[Transition]): list of transitions coming in the state.
        states (list[State]): list of the states directly contained by the state.
    """

    def __init__(self, name: str | None = None, parent_state: State | None = None, is_final: bool = False, location: Location | None = None):
        super().__init__('stateMachine.state', location)
        self.name: str | None = name
        self.parent_state: State | None = parent_state
        self.is_final = is_final
        self.outgoing_transitions: list[Transition] = []
        self.incoming_transitions: list[Transition] = []
        self.states = []

    def add_transitions(self, transitions: list[Transition]) -> None:
        for transition in transitions:
            self.outgoing_transitions.append(transition)

        for transition in transitions:
            transition.target.incoming_transitions.append(transition)

    def create_transition(self, target: State, input: str | None = None, output: str | None = None, location: Location | None = None) -> None:
        transition: Transition = Transition(
            self, target, input, output, location)
        self.outgoing_transitions.append(transition)
        target.incoming_transitions.append(transition)

    @abstractmethod
    def get_nested_initial_state(self) -> State:
        return self

    def get_depth(self) -> int:
        if self.parent_state is None:
            return 0
        else:
            return self.parent_state.get_depth()+1

    def construct_dict(self, attributes: dict, children: dict, refs: dict) -> dict:
        transitions: list[Transition] = list(filter(
            lambda transition: not transition.target.is_final, self.outgoing_transitions))
        final_transitions: list[Transition] = list(
            filter(lambda transition: transition.target.is_final, self.outgoing_transitions))

        return super().construct_dict(
            {
                'name': self.name,
                **attributes
            },
            {
                'transitions': list(map(lambda transition: transition.to_dict(), transitions)),
                'final transitions': list(map(lambda transition: transition.to_dict(), final_transitions)),
                **children
            },
            {**refs}
        )


class SimpleState(State):
    """State that contains no other states.
    """

    def __init__(self, name: str | None = None, parent_state: State | None = None, is_final: bool = False, location: Location | None = None):
        super().__init__(name, parent_state, is_final, location)

    def get_nested_initial_state(self) -> State:
        return super().get_nested_initial_state()

    def to_dict(self) -> dict:
        return super().construct_dict(
            {},
            {},
            {}
        )


class CompositeState(State):
    """State that can contain other states.

    Attributes:
        initial_state (InitialState): initial state of the composite state.
    """

    def __init__(self,  name: str, location: Location | None = None):
        super().__init__(name, None, False, location)
        self.initial_state: InitialState | None = None

    def get_nested_initial_state(self) -> State:
        if self.initial_state is None:
            raise ValueError('No initial state.')

        return self.initial_state.get_nested_initial_state()

    def to_dict(self) -> dict:
        if self.initial_state is None:
            raise ValueError('No initial state.')

        return super().construct_dict(
            {},
            {'states': list(map(lambda state: state.to_dict(), self.states))},
            {'initialState': self.initial_state.target.id}
        )


class InitialState:
    """Initial pseudo state.

    Attributes:
        target (State): target state of the outgoing transition from the initial pseudo state.
        parent_state (State): composite state containing the initial pseudo state. For initial states at the top-level, this attribute is None.
    """

    def __init__(self, target: State) -> None:
        self.target = target
        self.parent_state = target.parent_state

    def get_nested_initial_state(self) -> State:
        return self.target.get_nested_initial_state()


class Transition(ASTElement):
    """Represents a transition between two states.

    Attributes:
        source (State): source state of the transition.
        target (State): target state of the transition.
        input (str): input required to fire the transition.
        output (str): output produced when firing the transition.
    """

    def __init__(self, source: State, target: State, input: str | None = None, output: str | None = None, location: Location | None = None):
        super().__init__('stateMachine.transition', location)
        self.source = source
        self.target = target
        self.input = input
        self.output = output

    def to_dict(self) -> dict:
        refs: dict = {}

        if not self.target.is_final:
            refs['target'] = self.target.id

        return super().construct_dict(
            {
                'input': self.input,
                'ouptut': self.output
            },
            {},
            {**refs}
        )
