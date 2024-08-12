# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FeatureTransfer
                                 A QGIS plugin
 Feature Transfer Tool provides a seamless way to copy and paste features between layers.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-08-05
        copyright            : (C) 2024 by GIS Innovation Sdn. Bhd.
        email                : sales@gis.fm
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load FeatureTransfer class from file FeatureTransfer.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .featuretransfer import FeatureTransfer
    return FeatureTransfer(iface)
