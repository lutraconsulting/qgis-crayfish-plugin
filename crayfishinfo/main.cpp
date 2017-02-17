#include <iostream>

#include <QCoreApplication>
#include <QStringList>

#include "crayfish_capi.h"

int main(int argc, char *argv[]) {

    QCoreApplication app(argc, argv);
    QStringList cmdline_args = QCoreApplication::arguments();
    std::cout << "Crayfish loader " << CF_Version() << std::endl;

    if (cmdline_args.length() < 2) {
        std::cout << "Missing mesh file argument" << std::endl;
        std::cout << "crayfish mesh_file [dataset_file]" << std::endl;
        return 1;
    }

    // MESH
    QString mesh_file = cmdline_args[1];
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
    if (cmdline_args.length() > 2) {
        QString dataset_file = cmdline_args[2];
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
    return EXIT_SUCCESS;
}
