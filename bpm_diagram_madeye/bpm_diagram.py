import argparse
import itertools

from bpm_diagram_madeye.diagram_classes import Tag, Graph, Subprocess


def get_argparser():
    parser = argparse.ArgumentParser(description='Creates a dot/graphviz diagram from a BPMN file')

    parser.add_argument('input_file', help='The BPMN file to process')
    parser.add_argument('-o', '--output-file', help='The .dot file to write the diagram to')
    parser.add_argument('--exception-subprocess-name', help='The name of the subprocess for handling exceptions',
                        default='Handle Exception')
    parser.add_argument('--show-flows', action=argparse.BooleanOptionalAction,
                        help='Show the flow name on the edge label', default=False)
    parser.add_argument('--show-package-names', action=argparse.BooleanOptionalAction,
                        help='Show the package names for Java classes', default=False)
    parser.add_argument('--show-error-handling', action=argparse.BooleanOptionalAction,
                        help='Show error handling (adds much complexity)', default=False)
    parser.add_argument('--show-task-listeners', action=argparse.BooleanOptionalAction,
                        help='Show task listeners for userTasks', default=False)
    return parser


def remove_error_handling(graph, exception_subprocess_name):
    boundary_events = graph.get_child_nodes_with_tag(str(Tag('boundaryEvent')))
    event_ids = [event.id for event in boundary_events]

    exception_subprocesses = [subprocess for subprocess in graph if
                              isinstance(subprocess, Subprocess) and subprocess.name == exception_subprocess_name]
    sp_ids = [sp.id for sp in exception_subprocesses]
    downstream = [graph.get_downstream_nodes(sp_id) for sp_id in sp_ids]

    event_ids.extend(sp_ids)
    event_ids.extend(itertools.chain(*downstream))

    return graph.remove_adjacent(event_ids)


def main():
    parser = get_argparser()
    args = parser.parse_args()

    input_file = args.input_file
    output_file = args.output_file if args.output_file else f'{input_file}.dot'

    print(f'Input file: {input_file}')
    print(f'Output file: {output_file}')

    params = {'show_flows': args.show_flows,
              'show_package_names': args.show_package_names,
              'show_task_listeners': args.show_task_listeners}

    graph = Graph.load(input_file)

    if not args.show_error_handling:
        graph = remove_error_handling(graph, args.exception_subprocess_name)

    graph.save(output_file, params)

    print(f"{len(graph)} objects from {input_file} written to {output_file}")


if __name__ == '__main__':
    main()
