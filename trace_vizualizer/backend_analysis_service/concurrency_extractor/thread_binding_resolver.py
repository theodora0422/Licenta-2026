import re

from trace_vizualizer.domain.concurrency import (
    SourceLocation,
    ThreadClassInfo,
    ThreadInstanceInfo,
    ThreadStartBinding,
)


class ThreadBindingResolver:
    """
    Leagă:
    - instanțierile claselor de thread
    - apelurile start()
    - locația metodei run()

    Suportă în prima versiune:
    - GreedyThread t = new GreedyThread();
      t.start();

    - new GreedyThread().start();
    """

    def resolve(
        self,
        tree,
        source_code: str,
        thread_classes: list[ThreadClassInfo],
    ) -> tuple[list[ThreadInstanceInfo], list[ThreadStartBinding]]:
        class_map = self._build_class_map(thread_classes)

        instances = []
        bindings = []

        variable_to_instance = {}

        counters = {
            "instance": 1,
            "binding": 1,
        }

        self._walk(
            node=tree.root_node,
            source_code=source_code,
            class_map=class_map,
            variable_to_instance=variable_to_instance,
            instances=instances,
            bindings=bindings,
            counters=counters,
        )

        return instances, bindings

    def _walk(
        self,
        node,
        source_code: str,
        class_map: dict,
        variable_to_instance: dict,
        instances: list[ThreadInstanceInfo],
        bindings: list[ThreadStartBinding],
        counters: dict,
    ) -> None:
        if node.type == "variable_declarator":
            self._handle_variable_declarator(
                node=node,
                source_code=source_code,
                class_map=class_map,
                variable_to_instance=variable_to_instance,
                instances=instances,
                counters=counters,
            )

        if node.type == "method_invocation":
            self._handle_method_invocation(
                node=node,
                source_code=source_code,
                class_map=class_map,
                variable_to_instance=variable_to_instance,
                instances=instances,
                bindings=bindings,
                counters=counters,
            )

        child_index = 0
        while child_index < len(node.children):
            child = node.children[child_index]
            self._walk(
                node=child,
                source_code=source_code,
                class_map=class_map,
                variable_to_instance=variable_to_instance,
                instances=instances,
                bindings=bindings,
                counters=counters,
            )
            child_index = child_index + 1

    def _handle_variable_declarator(
        self,
        node,
        source_code: str,
        class_map: dict,
        variable_to_instance: dict,
        instances: list[ThreadInstanceInfo],
        counters: dict,
    ) -> None:
        text = self._node_text(node, source_code).strip()

        match = re.match(
            r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*new\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
            text,
        )

        if match is None:
            return

        variable_name = match.group(1)
        class_name = match.group(2)

        if class_name not in class_map:
            return

        instance_id = "instance_" + str(counters["instance"])
        counters["instance"] = counters["instance"] + 1

        instance = ThreadInstanceInfo(
            instance_id=instance_id,
            class_name=class_name,
            declared_name=variable_name,
            creation_location=self._build_source_location(node),
        )

        instances.append(instance)
        variable_to_instance[variable_name] = instance

    def _handle_method_invocation(
        self,
        node,
        source_code: str,
        class_map: dict,
        variable_to_instance: dict,
        instances: list[ThreadInstanceInfo],
        bindings: list[ThreadStartBinding],
        counters: dict,
    ) -> None:
        text = self._node_text(node, source_code).strip()

        if not text.endswith(".start()"):
            return

        receiver_text = text[:-8].strip()
        if receiver_text == "":
            return

        if receiver_text in variable_to_instance:
            instance = variable_to_instance[receiver_text]
            class_info = class_map.get(instance.class_name)

            binding_id = "binding_" + str(counters["binding"])
            counters["binding"] = counters["binding"] + 1

            binding = ThreadStartBinding(
                binding_id=binding_id,
                instance_id=instance.instance_id,
                class_name=instance.class_name,
                declared_name=instance.declared_name,
                start_location=self._build_source_location(node),
                run_method_location=class_info.run_method_location,
            )

            bindings.append(binding)
            return

        inline_match = re.match(
            r"^new\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)$",
            receiver_text,
        )

        if inline_match is None:
            return

        class_name = inline_match.group(1)
        if class_name not in class_map:
            return

        class_info = class_map[class_name]

        instance_id = "instance_" + str(counters["instance"])
        counters["instance"] = counters["instance"] + 1

        instance = ThreadInstanceInfo(
            instance_id=instance_id,
            class_name=class_name,
            declared_name=None,
            creation_location=self._build_source_location(node),
        )

        instances.append(instance)

        binding_id = "binding_" + str(counters["binding"])
        counters["binding"] = counters["binding"] + 1

        binding = ThreadStartBinding(
            binding_id=binding_id,
            instance_id=instance.instance_id,
            class_name=instance.class_name,
            declared_name=None,
            start_location=self._build_source_location(node),
            run_method_location=class_info.run_method_location,
        )

        bindings.append(binding)

    def _build_class_map(self, thread_classes: list[ThreadClassInfo]) -> dict:
        class_map = {}
        index = 0
        while index < len(thread_classes):
            info = thread_classes[index]
            class_map[info.class_name] = info
            index = index + 1
        return class_map

    def _node_text(self, node, source_code: str) -> str:
        return source_code[node.start_byte:node.end_byte]

    def _build_source_location(self, node) -> SourceLocation:
        return SourceLocation(
            start_line=node.start_point[0] + 1,
            start_column=node.start_point[1] + 1,
            end_line=node.end_point[0] + 1,
            end_column=node.end_point[1] + 1,
        )