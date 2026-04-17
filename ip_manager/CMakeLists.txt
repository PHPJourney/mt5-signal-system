cmake_minimum_required(VERSION 3.16)
project(IPManager VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Qt6 配置
find_package(Qt6 REQUIRED COMPONENTS Core Widgets Network Sql Gui)
qt_standard_project_setup()

# 源文件
set(SOURCES
    main.cpp
    src/core/ApplicationManager.cpp
    src/core/Database.cpp
    src/core/ConfigManager.cpp
    src/ai/AIGenerator.cpp
    src/ai/CodeAnalyzer.cpp
    src/ai/ImageProcessor.cpp
    src/payment/PaymentService.cpp
    src/payment/AlipayGateway.cpp
    src/payment/WechatGateway.cpp
    src/tracker/ProgressTracker.cpp
    src/tracker/CNIPATracker.cpp
    src/tracker/USPTOTracker.cpp
    src/network/HttpClient.cpp
    src/network/FileDownloader.cpp
    src/models/Application.cpp
    src/models/PaymentRecord.cpp
    src/models/TrackingLog.cpp
    src/utils/Logger.cpp
    src/utils/FileHelper.cpp
    ui/MainWindow.cpp
    ui/DashboardWidget.cpp
    ui/SoftwareCopyrightDialog.cpp
    ui/TrademarkDialog.cpp
    ui/PatentDialog.cpp
    ui/ProgressTrackerWidget.cpp
    ui/PaymentDialog.cpp
    ui/AIGeneratorWidget.cpp
)

set(HEADERS
    src/core/ApplicationManager.h
    src/core/Database.h
    src/core/ConfigManager.h
    src/ai/AIGenerator.h
    src/ai/CodeAnalyzer.h
    src/ai/ImageProcessor.h
    src/payment/PaymentService.h
    src/payment/AlipayGateway.h
    src/payment/WechatGateway.h
    src/tracker/ProgressTracker.h
    src/tracker/CNIPATracker.h
    src/tracker/USPTOTracker.h
    src/network/HttpClient.h
    src/network/FileDownloader.h
    src/models/Application.h
    src/models/PaymentRecord.h
    src/models/TrackingLog.h
    src/utils/Logger.h
    src/utils/FileHelper.h
    ui/MainWindow.h
    ui/DashboardWidget.h
    ui/SoftwareCopyrightDialog.h
    ui/TrademarkDialog.h
    ui/PatentDialog.h
    ui/ProgressTrackerWidget.h
    ui/PaymentDialog.h
    ui/AIGeneratorWidget.h
)

set(UI_FILES
    ui/MainWindow.ui
    ui/DashboardWidget.ui
    ui/SoftwareCopyrightDialog.ui
    ui/TrademarkDialog.ui
    ui/PatentDialog.ui
    ui/ProgressTrackerWidget.ui
    ui/PaymentDialog.ui
    ui/AIGeneratorWidget.ui
)

set(RESOURCES resources/ip_manager.qrc)

# 创建可执行文件
qt_add_executable(IPManager
    ${SOURCES}
    ${HEADERS}
    ${UI_FILES}
    ${RESOURCES}
)

# 链接 Qt 库
target_link_libraries(IPManager PRIVATE
    Qt6::Core
    Qt6::Widgets
    Qt6::Network
    Qt6::Sql
    Qt6::Gui
)

# 自动处理 MOC/UIC/RCC
set_target_properties(IPManager PROPERTIES
    AUTOMOC ON
    AUTOUIC ON
    AUTORCC ON
)

# Windows 特定设置
if(WIN32)
    set_target_properties(IPManager PROPERTIES
        WIN32_EXECUTABLE TRUE
    )
    # 复制 DLL
    qt_generate_deploy_app_script(
        TARGET IPManager
        FILENAME_VARIABLE deploy_script
        NO_UNSUPPORTED_PLATFORM_ERROR
    )
    install(SCRIPT ${deploy_script})
endif()

# macOS 特定设置
if(APPLE)
    set_target_properties(IPManager PROPERTIES
        MACOSX_BUNDLE TRUE
        MACOSX_BUNDLE_INFO_PLIST "${CMAKE_CURRENT_SOURCE_DIR}/Info.plist.in"
    )
endif()

# 安装
install(TARGETS IPManager
    BUNDLE DESTINATION .
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)