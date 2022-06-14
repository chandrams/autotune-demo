import os
import json
import csv
import sys
from io import StringIO
from hpo_helpers.utils import *

## Convert the tunable configs of JDK and Quarkus generated by HPO to JDK_JAVA_OPTIONS
## Input: HPO config json
## Output: JDK_JAVA_OPTIONS
def get_envoptions(hpoconfigjson):
    tunables_jvm_categorical = ["TieredCompilation", "AllowParallelDefineClass", "AllowVectorizeOnDemand", "AlwaysCompileLoopMethods", "AlwaysPreTouch", "AlwaysTenure", "BackgroundCompilation", "DoEscapeAnalysis", "UseInlineCaches", "UseLoopPredicate", "UseStringDeduplication", "UseSuperWord", "UseTypeSpeculation", "StackTraceInThrowable" , "nettyBufferCheck", "gc"]
    tunables_jvm_values = ["FreqInlineSize", "MaxInlineLevel", "MinInliningThreshold", "CompileThreshold", "CompileThresholdScaling", "ConcGCThreads", "InlineSmallCode", "LoopUnrollLimit", "LoopUnrollMin", "MinSurvivorRatio", "NewRatio", "TieredStopAtLevel", "MinHeapFreeRatio", "MaxHeapFreeRatio", "GCTimeRatio", "AdaptiveSizePolicyWeight"]
    tunables_quarkus = ["quarkus.thread-pool.core-threads", "quarkus.thread-pool.queue-size", "quarkus.datasource.jdbc.min-size", "quarkus.datasource.jdbc.max-size", "quarkus.hibernate-orm.jdbc.statement-fetch-size", "quarkus.http.io-threads"]
    JDK_JAVA_OPTIONS = ""

    with open(hpoconfigjson) as data_file:
        sstunables = json.load(data_file)

    for st in sstunables:
        for btunable in tunables_jvm_categorical:
            if btunable == st["tunable_name"]:
                if btunable == "nettyBufferCheck":
                    if st["tunable_value"] == "true":
                        JDK_JAVA_OPTIONS = JDK_JAVA_OPTIONS + " -Dio.netty.buffer.checkBounds=true -Dio.netty.buffer.checkAccessible=true"
                    else:
                        JDK_JAVA_OPTIONS = JDK_JAVA_OPTIONS + " -Dio.netty.buffer.checkBounds=false -Dio.netty.buffer.checkAccessible=false"
                elif btunable == "gc":
                    JDK_JAVA_OPTIONS = JDK_JAVA_OPTIONS + " -XX:+Use" + st["tunable_value"]
                else:
                    if st["tunable_value"] == "true":
                        JDK_JAVA_OPTIONS = JDK_JAVA_OPTIONS + " -XX:+" + btunable
                    elif st["tunable_value"] == "false":
                        JDK_JAVA_OPTIONS = JDK_JAVA_OPTIONS + " -XX:-" + btunable

        for jvtunable in tunables_jvm_values:
            if jvtunable == st["tunable_name"]:
                if jvtunable == "ConcGCThreads":
                    ## To avoid JVM exit if ParallelGCThreads < ConcGCThreads.
                    ## Only until dependencies between tunables are set.
                    JDK_JAVA_OPTIONS = JDK_JAVA_OPTIONS + " -XX:" + jvtunable + "=" + str(st["tunable_value"]) + " -XX:ParallelGCThreads=" + str(st["tunable_value"])
                else:
                    JDK_JAVA_OPTIONS = JDK_JAVA_OPTIONS + " -XX:" + jvtunable + "=" + str(st["tunable_value"])
                
        for qtunable in tunables_quarkus:
            if qtunable == st["tunable_name"]:
                if qtunable == "quarkus.datasource.jdbc.min-size":
                    # To avoid min-size < initial-size
                    JDK_JAVA_OPTIONS = JDK_JAVA_OPTIONS + " -D" + qtunable + "=" + str(st["tunable_value"]) + " -Dquarkus.datasource.jdbc.initial-size=" + str(st["tunable_value"])
                elif qtunable == "quarkus.http.io-threads":
                    if st["tunable_value"] == "true":
                        # Get cpu request value and use it. If cpurequest is not set, do not do anything.
                        #import hpo_helpers.utils; hpo_helpers.utils.get_tunablevalue(\"hpo_config.json\", \"cpuRequest\")"
                        old_stdout = sys.stdout
                        new_stdout = StringIO()
                        sys.stdout = new_stdout
                        get_tunablevalue("hpo_config.json", "cpuRequest")
                        cpu_req = new_stdout.getvalue()
                        sys.stdout = old_stdout
                        cpu_value = int(float(cpu_req))
                        if cpu_value != "":
                            JDK_JAVA_OPTIONS = JDK_JAVA_OPTIONS + " -Dhttp.io.threads=" + str(cpu_value)
                else:
                    JDK_JAVA_OPTIONS = JDK_JAVA_OPTIONS + " -D" + qtunable + "=" + str(st["tunable_value"])

    print(str(JDK_JAVA_OPTIONS))

