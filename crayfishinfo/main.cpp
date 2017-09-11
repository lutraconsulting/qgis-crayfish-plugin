#include <iostream>

#include <QCoreApplication>
#include <QStringList>
#include "crayfish_capi.h"

void help() {
    std::cout << "crayfishinfo mesh_file [-dDataset_file] [-eExpression] [-oOutputExpressionFilename] [-h]" << std::endl;
}

int main(int argc, char *argv[]) {

    QCoreApplication app(argc, argv);
    QStringList cmdline_args = QCoreApplication::arguments();
    std::cout << "Crayfish loader " << CF_Version() << std::endl;
    cmdline_args.takeFirst(); //Executable

    // parse arguments
    if (cmdline_args.length() < 2) {
        std::cout << "Missing mesh file argument" << std::endl;
        help();
        return 1;
    }   
    QString mesh_file = cmdline_args.takeFirst();
    QString dataset_file;
    QString expression;
    QString outputFilename;

    foreach (QString arg, cmdline_args) {
        if (arg.startsWith("-h")) {
            help();
            return 1;
        }
        if (arg.startsWith("-d")) {
            dataset_file = arg;
            dataset_file.remove(0, 2);
        }
        if (arg.startsWith("-e")) {
            expression = arg;
            expression.remove(0, 2);
        }
        if (arg.startsWith("-o")) {
            outputFilename = arg;
            outputFilename.remove(0, 2);
        }
    }

    // MESH
    std::cout << "Mesh File: " << mesh_file.toStdString() << std::endl;
    MeshH m = CF_LoadMesh(mesh_file.toStdString().c_str());
    if (m) {
        std::cout << "Mesh loaded: OK" << std::endl;       
    } else {
        std::cout << "Mesh loaded: ERR" << std::endl;
        std::cout << "Status err:" << CF_LastLoadError() <<  std::endl;
        std::cout << "Status warn:" << CF_LastLoadWarning() << std::endl;
        return 1;
    }

    // DATASET
    if (!dataset_file.isEmpty()) {
        std::cout << "Dataset File: " << dataset_file.toStdString() << std::endl;

        bool ok = CF_Mesh_loadDataSet(m, dataset_file.toStdString().c_str());
        if (ok) {
            std::cout << "Dataset loaded: OK" << std::endl;
        } else {
            std::cout << "Dataset loaded: ERR" << std::endl;
            std::cout << "Status err:" << CF_LastLoadError() <<  std::endl;
            std::cout << "Status warn:" << CF_LastLoadWarning() << std::endl;
            return 1;
        }
    }

    // STATS
    int nDatasets = CF_Mesh_dataSetCount(m);
    std::cout << std::endl << "Stats" << std::endl;
    std::cout << "  Node count: " << CF_Mesh_nodeCount(m) <<  std::endl;
    std::cout << "  Element count: " << CF_Mesh_elementCount(m) << std::endl;
    std::cout << "  Dataset count: " << nDatasets << std::endl;
    std::cout << "  Datasets: " << nDatasets << std::endl;
    for (int i=0; i<nDatasets; ++i) {
        DataSetH ds = CF_Mesh_dataSetAt(m, i);
        std::cout << "    " << CF_DS_name(ds) << " (" <<  CF_DS_outputCount(ds) << ")" << std::endl;
    }

    // Expression
    if (!expression.isEmpty()) {
        std::cout << "Expression: " << expression.toStdString() << std::endl;
        bool is_valid = CF_Mesh_calc_expression_is_valid(m, expression.toAscii());
        std::cout << "Is Valid: " << std::boolalpha << is_valid << std::endl;

        if (is_valid) {
            if (!outputFilename.isEmpty()) {
                double xmin, ymin, xmax, ymax;
                CF_Mesh_extent(m, &xmin, &ymin, &xmax, &ymax);
                double startTime = 0; //TODO
                double endTime = 0; // TODO
                bool add_to_dataset = false; //TODO
                bool res = CF_Mesh_calc_derived_dataset(m,
                                                        expression.toAscii(),
                                                        startTime, endTime,
                                                        xmin, ymin, xmax, ymax,
                                                        add_to_dataset,  outputFilename.toAscii());

                std::cout << "Exported " << std::boolalpha << res << " to " << outputFilename.toStdString() << std::endl;
            }
        }
    }

    return EXIT_SUCCESS;
}
