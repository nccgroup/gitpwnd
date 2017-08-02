import json
import os

# Helper class for
class IntelHelper:

    @staticmethod
    def parse_node_dir(node_dir):
        node_results = []

        for intel in os.listdir(node_dir):
            intel_file = os.path.join(node_dir, intel)

            with open(intel_file, 'r') as f:
                node_results.append(json.load(f))
                # parsed_json = json.load(f)
                # node_results[str(parsed_json["time_ran"])] = parsed_json

        return node_results

    @staticmethod
    def parse_repo_dir(repo_dir):
        intel = {}
        # In intel_dir, each subdirectory corresponds to a node_id, and each file in
        # a node's directory is a json file corresponding to what we've extracted.
        #
        # Filename of these individual intel files is currently the time when the extraction happened.

        for subdir in os.listdir(repo_dir):
            node_dir = os.path.join(repo_dir, subdir)
            intel[subdir] = IntelHelper.parse_node_dir(node_dir)

        return intel # this was fun to write

    # Returns:
    # {
    # "repo_name" => {
    #    "node_name" => [ intel_extracted1_json, intel_extracted2_json ],
    #    ...
    #  }
    # }
    @staticmethod
    def parse_all_intel_files(intel_dir):
        results = {}

        for subdir in os.listdir(intel_dir):
            repo_dir = os.path.join(intel_dir, subdir)

            results[subdir] = IntelHelper.parse_repo_dir(repo_dir)

        return results

    @staticmethod
    def json_prettyprint_intel(intel_dict):
        # intel_dict has the structure of the return value from parse_all_intel_files
        results = {}
        for repo_name, node_dict in intel_dict.items():
            tmp = {}
            for node_name, intel_list in node_dict.items():
                tmp[node_name] = [IntelHelper.annotate_intel_dict(x) for x in intel_list]

            results[repo_name] = tmp

        return results

    @staticmethod
    def annotate_intel_dict(intel_dict):
        # Turns each "value" for a node from: {'attr_name' => '<value>'} to
        # {'attr_name' => {'type' => '<type>', 'value' => '<value>'} }
        # where type := ['string' | 'json' | 'shell_command' | 'long_string']
        #   'long_string' = a string that's multiple lines
        #
        results = {}
        for intel_name, intel_value in intel_dict.items():
            intel_name = str(intel_name)

            if type(intel_value) is dict:
                if "stderr" in intel_value:
                    results[intel_name] = {"type": "shell_command",
                                           "value": {
                                               "stderr": str(intel_value["stderr"]),
                                               "stdout": str(intel_value["stdout"])
                                           }}
                else:
                    results[intel_name] = { "type": "json",
                                            "value": json.dumps(intel_value, sort_keys=True, indent=4, separators=(',', ': '))}
            elif intel_value.count("\n") > 0:
                results[intel_name] = {"type": "long_string",
                                       "value": str(intel_value)}
            else:
                results[intel_name] = {"type": "string",
                                       "value": str(intel_value)}

        return results
