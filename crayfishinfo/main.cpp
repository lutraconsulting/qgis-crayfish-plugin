#include <iostream>

#include <QCoreApplication>
#include <QStringList>
#include "crayfish_capi.h"
#include <limits>
#include "geos_c.h"

void help() {
    std::cout << "crayfishinfo mesh_file [-dDataset_file] [-eExpression] [-oOutputExpressionFilename] [-h]" << std::endl;
}

int test_mask_filter() {
    //const char* path = "/lutra/qgis-crayfish-plugin/test/data/tuflow/dat/dat_format_d.dat";


    QString mesh_file = "/home/vsklencar/lutra/qgis-crayfish-plugin/test/data/NetCDF/indonesia_nc3_copy.nc";
    QString dataset_file;
    QString expression = "\"Total cloud cover\"";
    QString outputFilename = "/home/vsklencar/lutra/qgis-crayfish-plugin/test/data/NetCDF/test1.dat";

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

        const char* mask_wkt= "Polygon ((113.76902949571837098 8.44005708848715663, 128.57159847764035021 3.9110371075166519, 121.77806850618458157 -1.31731684110370928, 113.868934348239776 -0.78449096098953142, 113.76902949571837098 8.44005708848715663))";

        if (is_valid) {
            if (!outputFilename.isEmpty()) {
                double xmin, ymin, xmax, ymax;
                CF_Mesh_extent(m, &xmin, &ymin, &xmax, &ymax);
                double startTime = -std::numeric_limits<float>::max();
                double endTime = std::numeric_limits<float>::max();
                bool add_to_dataset = true;
                 std::cout << "Calcl init " << std::endl;
                 bool res = false;
                 if (true) {
                     res = CF_Mesh_calc_derived_dataset_with_mask(m,
                                                             expression.toAscii(),
                                                             startTime, endTime,
                                                             mask_wkt,
                                                             add_to_dataset,  outputFilename.toAscii());
                 } else {
                                     res = CF_Mesh_calc_derived_dataset(m,
                                                                             expression.toAscii(),
                                                                             startTime, endTime,
                                                                             xmin, xmax, ymin, ymax,
                                                                             add_to_dataset,  outputFilename.toAscii());
                 }




                std::cout << "Exported " << std::boolalpha << res << " to " << outputFilename.toStdString() << std::endl;
            }
        }
    }

    return 0;
}

int example() {

    GEOSWKTReader *reader;
        GEOSGeometry* polygon1;
        GEOSGeometry* polygon2;

        const GEOSPreparedGeometry* prepared1;

        initGEOS(NULL, NULL);

        reader = GEOSWKTReader_create();

        if ( ! reader ) {
            std::cout << "Error while GEOS has been initializing." << std::endl;
        }

        polygon1 = GEOSWKTReader_read(reader, "POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))");
        polygon2 = GEOSWKTReader_read(reader, "POLYGON EMPTY");
        //const char* pointWkt = "POINT((100,6))";
        const char* pointWkt = "POINT (1.0000000000000000 2.0000000000000000)";

        GEOSGeometry* point = GEOSWKTReader_read(reader, pointWkt);

        char a = GEOSContains(polygon1, polygon2);
        if (a == 0) {
            printf("false\n");
        } else if(a == 1) {
            printf("true\n");
        } else {
            printf("error\n");
        }

        prepared1 = GEOSPrepare(polygon1);

        char b = GEOSPreparedContains(prepared1, polygon2);
        if (b == 0) {
            printf("false\n");
        } else if(b == 1) {
            printf("true\n");
        } else {
            printf("error\n");
        }

        return 0;
}


int test_intersection() {
    std::cout << "test_intersection" << std::endl;
    initGEOS(NULL, NULL);
    //GEOSContextHandle_t handle = GEOS_init_r();
    GEOSGeometry* pointGeom;
    GEOSGeometry* maskGeom;
    GEOSWKTReader* reader = GEOSWKTReader_create();

    if ( ! reader ) {
        std::cout << "Error while GEOS has been initializing." << std::endl;
    }

    //const char* pointWkt = "Point (-200.2655785411116689 51.41663308002466692)";
    const char* pointWkt = "Point (-2.2655785411116689 51.41663308002466692)";
    const char* maskWkt = "Polygon ((-2.26570857780532053 51.41666399122910036, -2.26545457024735075 51.41671712371006464, -2.26533433281120766 51.41667157702460145, -2.26535121337009704 51.41648511873184191, -2.26562469704825986 51.41644586769574943, -2.26586421342017719 51.41649563566220849, -2.26570857780532053 51.41666399122910036))";

    pointGeom = GEOSWKTReader_read(reader, pointWkt);
    maskGeom = GEOSWKTReader_read(reader, maskWkt);

    std::cout << "Going to test intersection." << std::endl;

    GEOSGeometry* geom = GEOSIntersection(maskGeom, pointGeom);
    std::cout << "Final geom generated." << std::endl;

    char a = GEOSContains(maskGeom, pointGeom);
      if (a == 0) {
          printf("false\n");
      } else if(a == 1) {
          printf("true\n");
      } else {
          printf("error\n");
      }

    std::cout << "Result " << a <<std::endl;

    if ( ! geom ) {
        std::cout << "Not intersecting, an error occured." << std::endl;
    }

    GEOSWKTReader_destroy(reader);
    //GEOS_finish_r(handle);

    return 0;
}

int main(int argc, char *argv[]) {

    QCoreApplication app(argc, argv);
    QStringList cmdline_args = QCoreApplication::arguments();
    std::cout << "Crayfish loader " << CF_Version() << std::endl;
    cmdline_args.takeFirst(); //Executable

    test_intersection();
    example();
    test_mask_filter();

    // parse arguments
    if (cmdline_args.length() < 1) {
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
                double startTime = -std::numeric_limits<float>::max();
                double endTime = std::numeric_limits<float>::max();
                bool add_to_dataset = false;
                bool res = CF_Mesh_calc_derived_dataset(m,
                                                        expression.toAscii(),
                                                        startTime, endTime,
                                                        xmin, xmax, ymin, ymax,
                                                        add_to_dataset,  outputFilename.toAscii());

                std::cout << "Exported " << std::boolalpha << res << " to " << outputFilename.toStdString() << std::endl;
            }
        }
    }

    return EXIT_SUCCESS;
}
