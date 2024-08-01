import re
from functools import partial

from lxml import etree


def handle_subProcess(element):
    if Graph.element_is_subprocess(element):
        return Subprocess.from_element(element)
    else:
        raise UnsuitableHandlerException


def handle_boundaryEvent(element):
    if element.tag == str(Tag('boundaryEvent')):
        return BoundaryEvent.from_element(element)
    else:
        raise UnsuitableHandlerException


def handle_serviceTask(element):
    if element.tag == str(Tag('serviceTask')):
        return ServiceTask.from_element(element)
    else:
        raise UnsuitableHandlerException


def handle_userTask(element):
    if element.tag == str(Tag('userTask')):
        return UserTask.from_element(element)
    else:
        raise UnsuitableHandlerException


def handle_callActivity(element):
    if element.tag == str(Tag('callActivity')):
        return CallActivity.from_element(element)
    else:
        raise UnsuitableHandlerException


def handle_intermediateCatchEvent(element):
    if element.tag == str(Tag('intermediateCatchEvent')):
        return IntermediateCatchEvent.from_element(element)
    else:
        raise UnsuitableHandlerException


def handle_coloured_node(colour, element):
    node = handle_node(element)
    node.colour = colour
    return node


def handle_node(element):
    if Graph.element_has_attribs(element, ['id']):
        return Node.from_element(element)
    else:
        raise UnsuitableHandlerException


def handle_edge(element):
    if Graph.element_has_attribs(element, ['id', 'sourceRef', 'targetRef']):
        return Edge.from_element(element)
    else:
        raise UnsuitableHandlerException


def handle_gateway(element):
    return Gateway.from_element(element)


class BpmDiagramException(Exception):
    pass


class UnsuitableHandlerException(BpmDiagramException):
    pass


class Tag:
    BPMN_NAMESPACE = 'http://www.omg.org/spec/BPMN/20100524/MODEL'
    __TAG_REGEX = re.compile("^{(.*)}(.*)$")

    def __init__(self, tag, namespace=BPMN_NAMESPACE):
        self.namespace = namespace
        self.tag = tag

    @classmethod
    def from_string(cls, tag_str):
        regex_result = Tag.__TAG_REGEX.match(tag_str)
        namespace = regex_result.group(1)
        tagname = regex_result.group(2)

        return Tag(tagname, namespace=namespace)

    @classmethod
    def from_element(cls, element):
        return Tag.from_string(element.tag)

    def __repr__(self):
        return f'{{{self.namespace}}}{self.tag}'


class Graph:
    DOT_HEADERS = [
        'fontname = "sans"',
        'node[shape = "box", fontname = "sans"]',
        'edge[fontname = "sans"]'
    ]

    OTHER_HANDLERS = [
        handle_edge,
        handle_node
    ]

    TAG_HANDLERS = {
        'exclusiveGateway': handle_gateway,
        'parallelGateway': handle_gateway,
        'startEvent': partial(handle_coloured_node, '#d1ffd1'),
        'endEvent': partial(handle_coloured_node, '#ffd1d1')
    }

    def __init__(self, root=None):
        self.__graph = {}

        if root is not None:
            for element in root:
                self.add_element(element)

    def add_element(self, element):
        item = Graph.__process_element(element)
        self.__add_item(item)

    def to_dot(self, graph=None, params=None):
        return '\n'.join([item.to_dot(graph=graph, params=params) for item in self.__graph.values()])

    def __add_item(self, item):
        if item:
            self.__graph[item.id] = item

    def save(self, output_file, params):
        with open(output_file, 'w') as file:
            file.write('digraph G {\n')

            for header in Graph.DOT_HEADERS:
                file.write(header)
                file.write('\n')

            file.write(self.to_dot(graph=self.__graph, params=params))

            file.write('}\n')

    @classmethod
    def load(cls, input_file):
        bpm_data = etree.parse(input_file)
        process_elements = bpm_data.xpath('//bpm:process', namespaces={'bpm': Tag.BPMN_NAMESPACE})

        if len(process_elements) != 1:
            raise RuntimeError(f"{len(process_elements)} process elements found - 1 expected")

        return Graph(process_elements[0])

    def get_child_nodes(self):
        child_nodes = [child for child in self.__graph.values() if isinstance(child, Node)]

        return child_nodes

    def get_first_node(self):
        return self.get_child_nodes()[0]

    def get_last_node(self):
        return self.get_child_nodes()[-1]

    def get_child_nodes_with_tag(self, tag):
        return [node for node in self.get_child_nodes() if node.tag == tag]

    def get_item(self, item_id):
        return self.__graph.get(item_id)

    def remove_adjacent(self, id_list):
        result = Graph()
        id_set = set(id_list)
        for _, item in self.__graph.items():
            adjacent_set = set(item.adjacent)
            if not id_set.intersection(adjacent_set):
                result.__add_item(item)

        return result

    @property
    def ids(self):
        return list(self.__graph.keys())

    def __len__(self):
        return len(self.__graph)

    def __iter__(self):
        return self.__graph.values().__iter__()

    @classmethod
    def element_get_children_with_tag(cls, element, tag):
        return [item for item in element if item.tag == str(tag)]

    @classmethod
    def element_get_first_child_with_tag(cls, element, tag):
        matches = Graph.element_get_children_with_tag(element, tag)

        return matches[0] if matches else None

    @classmethod
    def __get_handler_fn(cls, element):
        tag = Tag.from_element(element)

        try:
            fn_name = f'handle_{tag.tag}'
            return globals()[fn_name]
        except KeyError:
            return Graph.TAG_HANDLERS.get(tag.tag)

    @classmethod
    def element_has_attribs(cls, element, attribs):
        attribs = [element.attrib.get(attrib) for attrib in attribs]

        return all(attribs)

    @classmethod
    def element_is_subprocess(cls, element):
        return element.tag == str(Tag('subProcess'))

    @classmethod
    def __process_element(cls, element):
        handler_fn = Graph.__get_handler_fn(element)

        if handler_fn:
            return handler_fn(element)
        else:
            for handler_fn in Graph.OTHER_HANDLERS:
                try:
                    return handler_fn(element)
                except UnsuitableHandlerException:
                    pass

    def get_edges(self, source_id=None, target_id=None):
        edges = [item for item in self.__graph.values() if isinstance(item, Edge)]

        if source_id:
            edges = [edge for edge in edges if edge.source_node == source_id]

        if target_id:
            edges = [edge for edge in edges if edge.target_node == target_id]

        return edges

    def get_downstream_nodes(self, node_id):
        edges = [edge for edge in self.get_edges(source_id=node_id)]

        return [edge.target_node for edge in edges]


class Node:
    def __init__(self, node_id, tag, name, show_id=True, colour=None, extras=None):
        self.id = node_id
        self.__tag = tag
        self.__name = name if name else '<no_name>'
        self.__show_id = show_id
        self.__colour = colour
        self.__extras = extras

    @classmethod
    def from_element(cls, element):
        return Node(element.attrib['id'], element.tag, element.attrib.get('name'))

    def to_dot(self, graph=None, params=None):
        colour_text = f', fillcolor="{self.__colour}", style="filled"' if self.__colour else ''
        return f'{self.id} [label="{self.get_label(params=params)}", shape="{self.get_shape()}"{colour_text}]'

    def get_label(self, params=None, include_extras=True):
        extras_label = '\n' + '\n'.join(
            [f'{item[0]}: {item[1]}' for item in self.__extras.items()]) if self.__extras and include_extras else ''
        return f'{self.__name}\\nid: {self.id}{extras_label}' if self.__show_id else self.__name

    def get_shape(self, params=None):
        return 'box'

    @property
    def start_node_id(self):
        return self.id

    @property
    def tag(self):
        return self.__tag

    @property
    def end_node_id(self):
        return self.id

    @property
    def adjacent(self):
        return [self.id]

    @property
    def colour(self):
        return self.__colour

    @colour.setter
    def colour(self, colour):
        self.__colour = colour

    def get_extra(self, extra_name):
        return self.__extras.get(extra_name)


class Edge:
    def __init__(self, edge_id, source_node, target_node, name=None, condition=None):
        self.id = edge_id
        self.__name = name
        self.__source_node = source_node
        self.__target_node = target_node
        self.__condition = condition

    @classmethod
    def __tidy_condition(cls, condition_text):
        line_break = ['&&', '||', '==']
        if condition_text.startswith('${'):
            condition_text = condition_text[2:]
        if condition_text.endswith('}'):
            condition_text = condition_text[:-1]
        result = condition_text.replace('"', '\\"')

        for item in line_break:
            result = result.replace(item, item + '\\n')

        return result

    @classmethod
    def __get_condition(cls, element):
        condition = Graph.element_get_first_child_with_tag(element, Tag('conditionExpression'))
        return Edge.__tidy_condition(condition.text) if condition is not None else None

    @classmethod
    def from_element(cls, element):
        condition_text = Edge.__get_condition(element)
        return Edge(element.attrib['id'], element.attrib['sourceRef'], element.attrib['targetRef'],
                    name=element.attrib.get('name'), condition=condition_text)

    def to_dot(self, graph=None, params=None):
        show_flows = params.get('show_flows') if params else False
        if graph:
            source_node = graph.get(self.__source_node).end_node_id if graph.get(
                self.__source_node) else self.__source_node
            target_node = graph.get(self.__target_node).start_node_id if graph.get(
                self.__target_node) else self.__target_node
        else:
            source_node = self.__source_node
            target_node = self.__target_node

        label_components = []

        if self.__name:
            label_components.append(self.__name)
        if self.__condition:
            label_components.append(self.__condition)
        if show_flows:
            label_components.append(self.id)

        if label_components:
            label_text = '\\n'.join(label_components)
        else:
            label_text = None

        label = f' [label="{label_text}"]' if label_text else ''

        return f'{source_node} -> {target_node}{label}'

    @property
    def adjacent(self):
        return [self.__source_node, self.__target_node]

    @property
    def source_node(self):
        return self.__source_node

    @property
    def target_node(self):
        return self.__target_node


class Subprocess:
    __subgraph_index = 0

    def __init__(self, id, name, children):
        self.id = id
        self.__name = name
        self.__children = children
        self.__start_node = self.__children.get_child_nodes_with_tag(str(Tag('startEvent')))[0]
        self.__end_node = self.__children.get_child_nodes_with_tag(str(Tag('endEvent')))[0]
        self.__index = Subprocess.__get_subgraph_index()

    @classmethod
    def from_element(cls, element):
        children = Graph(element)

        return Subprocess(element.attrib['id'], element.attrib['name'], children)

    @property
    def start_node_id(self):
        return self.__start_node.id

    @property
    def end_node_id(self):
        return self.__end_node.id

    def to_dot(self, graph=None, params=None):
        result = [f'subgraph cluster{self.__index} {{', f'label="{self.__name}"']
        result.append('style="filled"\n')
        result.append('fillcolor="#f2f2f2"')
        result.append(self.__children.to_dot(graph=graph, params=params))
        result.append('}\n')

        return '\n'.join(result)

    @classmethod
    def __get_subgraph_index(cls):
        result = cls.__subgraph_index
        cls.__subgraph_index = result + 1
        return result

    @property
    def adjacent(self):
        result = [self.id]
        result.extend(self.__children.ids)
        return result

    @property
    def name(self):
        return self.__name


class BoundaryEvent(Node):
    def __init__(self, node_id, tag, name, attached):
        super().__init__(node_id, tag, name, show_id=False)
        self.__attached = attached

    def to_dot(self, graph=None, params=None):
        edge = Edge('boundary', self.__attached, self.id)
        return f'{self.id} [shape="circle", label="~"]\n' + edge.to_dot(graph=graph, params=params)

    @classmethod
    def from_element(cls, element):
        return BoundaryEvent(element.attrib['id'], element.tag, element.attrib['name'], element.attrib['attachedToRef'])


class Gateway(Node):
    __LABELS = {
        'exclusiveGateway': 'X',
        'parallelGateway': '+'
    }

    def __init__(self, node_id, tag, name):
        super().__init__(node_id, tag, name)

    def to_dot(self, graph=None, params=None):
        tag = Tag.from_string(self.tag)
        label = Gateway.__LABELS.get(tag.tag)

        return f'{self.id} [shape="diamond", label="{label}"]'

    @classmethod
    def from_element(self, element):
        name = element.attrib.get('name')
        return Gateway(element.attrib['id'], element.tag, name)


class ServiceTask(Node):
    def __init__(self, node_id, tag, name, java_class):
        extras = {'class': java_class}
        super().__init__(node_id, tag, name, colour='#d1f4ff', extras=extras)

    @classmethod
    def from_element(self, element):
        java_class = element.attrib.get('{http://activiti.org/bpmn}class')

        return ServiceTask(element.attrib['id'], element.tag, element.attrib['name'], java_class)

    def get_label(self, params=None):
        label = super().get_label(params=params, include_extras=False)
        java_class = self.get_extra('class')

        if java_class:
            if not params or not params.get('show_package_names'):
                java_label = java_class.split('.')[-1]
            else:
                java_label = java_class

            return f'{label}\\nclass: {java_label}'
        else:
            return label


class TaskListener:
    def __init__(self, event, class_name=None, expression=None):
        self.event = event
        self.class_name = class_name
        self.expression = expression

    @classmethod
    def from_element(self, element):
        class_name = element.attrib.get('class')
        expression = element.attrib.get('expression')
        return TaskListener(element.attrib['event'], class_name=class_name, expression=expression)


class UserTask(Node):
    def __init__(self, node_id, tag, name, task_listeners=None):
        super().__init__(node_id, tag, name, colour='#e8d1ff')
        self.__task_listeners = task_listeners

    @classmethod
    def from_element(cls, element):
        task_listeners = [TaskListener.from_element(sub_element) for sub_element in
                          element.findall('.//{http://activiti.org/bpmn}taskListener')]

        return UserTask(element.attrib['id'], element.tag, element.attrib['name'], task_listeners)

    def get_shape(self, params=None):
        return 'ellipse'

    def __get_class_name(self, class_name, params):
        if not params or not params.get('show_package_names'):
            return class_name.split('.')[-1]
        else:
            return class_name

    def get_label(self, params=None):
        label = super().get_label()
        if not params or params.get('show_task_listeners'):
            task_listener_text = '\n' + '\n'.join(
                [f'{listener.event}: {self.__get_class_name(listener.class_name, params=params)}' for listener in
                 self.__task_listeners]) if self.__task_listeners else ''
        else:
            task_listener_text = ''
        return label + task_listener_text


class CallActivity(Node):
    def __init__(self, node_id, tag, name, called_element):
        extras = {'calling': called_element}
        super().__init__(node_id, tag, name, colour='#ffffd1', extras=extras)

    @classmethod
    def from_element(cls, element):
        return CallActivity(element.attrib['id'], element.tag, element.attrib['name'], element.attrib['calledElement'])


class IntermediateCatchEvent(Node):
    def __init__(self, node_id, tag, name, extras=None):
        super().__init__(node_id, tag, name, colour='#ffd1f4', extras=extras)

    @classmethod
    def from_element(self, element):
        extras = IntermediateCatchEvent.__get_extras(element)

        return IntermediateCatchEvent(element.attrib['id'], element.tag, element.attrib['name'], extras)

    @classmethod
    def __get_extras(cls, element):
        extras = {}

        message_event_definitions = element.findall(f'.//{str(Tag("messageEventDefinition"))}')
        if message_event_definitions:
            extras['messageRef'] = message_event_definitions[0].attrib['messageRef']

        timer_durations = element.findall(f'.//{str(Tag("timeDuration"))}')
        if timer_durations:
            extras['duration'] = timer_durations[0].text

        return extras
