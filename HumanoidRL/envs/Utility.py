import pybullet as p
import pybullet_data
import numpy as np
import time
import os


class Utility:
    '''
    Class containing all the helper functions
    '''
    def __init__(self):
        '''
        joinIndex
        - A dictionary mapping Joint name to it's index in urdf file
        '''
        self.jointIndex = {
            'LHipYawPitch': (13, 0),
            'LHipRoll': (14, 1),
            'LHipPitch': (15, 2),
            'LKneePitch': (16, 3),
            'LAnklePitch': (17, 4),
            'LAnkleRoll': (18, 5),
            'RHipYawPitch': (26, 6),
            'RHipRoll': (27, 7),
            'RHipPitch': (28, 8),
            'RKneePitch': (29, 9),
            'RAnklePitch': (30, 10),
            'RAnkleRoll': (31, 11),
            'LShoulderPitch': (39, 12),
            'LShoulderRoll': (40, 13),
            'LElbowYaw': (41, 14),
            'LElbowRoll': (42, 15),
            'RShoulderPitch': (56, 16),
            'RShoulderRoll': (57, 17),
            'RElbowYaw': (58, 18),
            'RElbowRoll': (59, 19)
        }
        self.jointPos = np.zeros((len(self.jointIndex), 1))
        self.jointVel = np.zeros((len(self.jointIndex), 1))
        self.jointF = np.zeros((len(self.jointIndex), 3))
        self.jointT = np.zeros((len(self.jointIndex), 3))
        self.appliedT = np.zeros((len(self.jointIndex), 1))
        self.bodyPos = np.zeros((1, 3))
        self.bodyAng = np.zeros((1, 3))
        self.bodyVel = np.zeros((1, 3))
        self.bodyAngVel = np.zeros((1, 3))
        self.observation = np.empty((len(self.jointIndex)+3, 1))
        self.nao = None

    def init_bot(self, freq):
        """Initialising the paramters of bot and simulation
        INPUT_VARIABLES
            freq : freq of the simlulation should be arounf 50-100
        """
        # p.GUI for debug visualizer and p.DIRECT for non graphical version
        # ex. while running on server
        p.connect(p.GUI)
        p.setGravity(0, 0, -9.81)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.loadURDF("plane.urdf")
        p.configureDebugVisualizer(p.COV_ENABLE_RENDERING, 0)

        self.startPos = [0, 0, .35]
        path = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "../humanoid/nao.urdf")
        self.nao = p.loadURDF(path, self.startPos,
                              flags=p.URDF_USE_SELF_COLLISION_EXCLUDE_PARENT)

        self.init_joints()
        p.configureDebugVisualizer(p.COV_ENABLE_RENDERING, 1)
        self.timeStep = 1./freq

    def reset_bot(self):

        p.configureDebugVisualizer(p.COV_ENABLE_RENDERING, 0)
        p.resetBasePositionAndOrientation(self.nao, self.startPos, p.getQuaternionFromEuler([0,0,0]))
        self.init_joints()
        p.configureDebugVisualizer(p.COV_ENABLE_RENDERING, 1)
        
    def init_joints(self):
        """Initialising the starting joint values"""
        for joint, index in self.jointIndex.items():
            p.setJointMotorControl2(self.nao, index[0], p.POSITION_CONTROL,
                                    targetPosition=0, force=1000)
            p.enableJointForceTorqueSensor(self.nao, index[0], enableSensor=1)
        shoulderPitch = np.pi / 2.
        shoulderRoll = 0.1
        # this makes the arms hang down and not forward
        p.setJointMotorControl2(self.nao, 56, p.POSITION_CONTROL,
                                targetPosition=shoulderPitch, force=1000)
        p.setJointMotorControl2(self.nao, 39, p.POSITION_CONTROL,
                                targetPosition=shoulderPitch, force=1000)
        p.setJointMotorControl2(self.nao, 57, p.POSITION_CONTROL,
                                targetPosition=-shoulderRoll, force=1000)
        p.setJointMotorControl2(self.nao, 40, p.POSITION_CONTROL,
                                targetPosition=shoulderRoll, force=1000)

    def execute_frame(self, action):
        """To take an action on the bot
        INPUT_VARIABLES
            action : A list containing the final positions of all the
                     joints"""
        for joint, index in self.jointIndex.items():
            pos = (np.pi / 2.) * action[index[1]]
            # Function to move a joint at a specific position
            p.setJointMotorControl2(
                self.nao, index[0], p.POSITION_CONTROL, targetPosition=pos)
        p.stepSimulation()
        time.sleep(self.timeStep)

    def get_observation(self):
        """Getting the joint values"""
        self.update_joints()
        self.observation[:, :] = np.vstack((self.jointPos, self.bodyPos.T))
        return self.observation.T

    def update_joints(self):
        for joint, index in self.jointIndex.items():
            temp = p.getJointState(self.nao, index[0])
            self.jointPos[index[1], :] = temp[0]
            self.jointVel[index[1], :] = temp[1]
            self.jointF[index[1], :] = temp[2][:3]
            self.jointT[index[1], :] = temp[2][:-3]
            self.appliedT[index[1], :] = temp[3]
        self.bodyPos[:, :], temp = p.getBasePositionAndOrientation(self.nao)
        self.bodyAng[:, :] = p.getEulerFromQuaternion(temp)
        self.bodyVel[:, :], self.bodyAngVel[:, :] = p.getBaseVelocity(self.nao)

    def kill_bot(self):
        """To disconnect from the server"""
        p.disconnect()
