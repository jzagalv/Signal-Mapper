
from PyQt5.QtWidgets import QDockWidget, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt

class ProjectTreeDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Proyecto", parent)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.setWidget(self.tree)

    def build(self, project):
        self.tree.clear()
        if not project:
            return
        for bay in project.bays.values():
            bay_item = QTreeWidgetItem([bay.name])
            bay_item.setData(0, Qt.UserRole, ("BAY", bay.bay_id))
            self.tree.addTopLevelItem(bay_item)
            for dev in bay.devices.values():
                dev_item = QTreeWidgetItem([dev.name])
                dev_item.setData(0, Qt.UserRole, ("DEV", bay.bay_id, dev.device_id))
                bay_item.addChild(dev_item)
        self.tree.expandAll()
