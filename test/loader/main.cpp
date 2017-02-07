#include <iostream>

#include <QCoreApplication>
#include <QStringList>

#include "crayfish_capi.h"

int main(int argc, char *argv[]) {

    QCoreApplication app(argc, argv);
    QStringList cmdline_args = QCoreApplication::arguments();
    std::cout << "Crayfish loader " << CF_Version() << std::endl;

    if (cmdline_args.length() != 2) {
        std::cout << "Missing mesh file argument" << std::endl;
        return 1;
    }
    QString path = cmdline_args[1];
    std::cout << "File: " << path.toStdString() << std::endl;

    MeshH m = CF_LoadMesh(path.toStdString().c_str());
    if (m) {
        std::cout << "Mesh loaded: OK" << std::endl;
    } else {
        std::cout << "Mesh loaded: ERR" << std::endl;
        std::cout << "Status err:" << CF_LastLoadError() <<  std::endl;
        std::cout << "Status warn:" << CF_LastLoadWarning() << std::endl;
    }

    return EXIT_SUCCESS;
}
