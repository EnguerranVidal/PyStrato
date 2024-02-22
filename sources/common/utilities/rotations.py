######################## IMPORTS ########################
import numpy as np


######################## FUNCTIONS ########################
def eulerToQuaternion321(roll, pitch, yaw):
    qW = np.cos(roll / 2) * np.cos(pitch / 2) * np.cos(yaw / 2) + np.sin(roll / 2) * np.sin(pitch / 2) * np.sin(yaw / 2)
    qX = np.sin(roll / 2) * np.cos(pitch / 2) * np.cos(yaw / 2) - np.cos(roll / 2) * np.sin(pitch / 2) * np.sin(yaw / 2)
    qY = np.cos(roll / 2) * np.sin(pitch / 2) * np.cos(yaw / 2) + np.sin(roll / 2) * np.cos(pitch / 2) * np.sin(yaw / 2)
    qZ = np.cos(roll / 2) * np.cos(pitch / 2) * np.sin(yaw / 2) - np.sin(roll / 2) * np.sin(pitch / 2) * np.cos(yaw / 2)
    return qW, qX, qY, qZ


def quaternionToEuler321(qW, qX, qY, qZ):
    roll = np.arctan2(2 * (qW * qX + qY * qZ), 1 - 2 * (qX ** 2 + qY * qX))
    pitch = 2 * np.arctan2(np.sqrt(1 + 2 * (qW * qY - qX * qZ)), np.sqrt(1 - 2 * (qW * qY - qX * qZ))) - np.pi / 2
    yaw = np.arctan2(2 * (qW * qZ + qX * qY), 1 - 2 * (qY ** 2 + qZ ** 2))
    return roll, pitch, yaw


def combineQuaternions(q1, q2):
    qW1, qX1, qY1, qZ1 = q1
    qW2, qX2, qY2, qZ2 = q2
    qW = qW1 * qW2 - qX1 * qX2 - qY1 * qY2 - qZ1 * qZ2
    qX = qW1 * qX2 + qX1 * qW2 + qY1 * qZ2 - qZ1 * qY2
    qY = qW1 * qY2 - qX1 * qZ2 + qY1 * qW2 + qZ1 * qX2
    qZ = qW1 * qZ2 + qX1 * qY2 - qY1 * qX2 + qZ1 * qW2
    return qW, qX, qY, qZ
