Vision16__LIME = Signature (1, -6571, -5693, -6132, -3053, -2661, -2857, 2.5, 0)
Vision16__MANGO = Signature (2, 3641, 5393, 4517, -2541, -2241, -2391, 2.5, 0)
Vision16__LEMON = Signature (3, 1193, 2485, 1839, -3569, -3375, -3472, 2.5, 0)
vision Vision16 = Vision (PORT16, 50, Vision16__LIME, Vision16__MANGO, Vision16__LEMON)




# ---------------------------------------------------------------------------- #
#                                                                              #
# 	Module:       main.py                                                      #
# 	Author:       krizz                                                        #
# 	Created:      12/4/2024, 5:08:37 PM                                        #
# 	Description:  V5 project                                                   #
#                                                                              #
# ---------------------------------------------------------------------------- #

# Library imports
from vex import *

# States
IDLE = 0
LINE = 1
SEARCHING = 2
APPROACHING = 3
COLLECTING = 4
RETURNING = 5

currentState = IDLE

# Counter
i = 0

# Initialization
brain = Brain()

controller = Controller()

ultraSonic = Sonar(brain.three_wire_port.g)

leftLine = Line(brain.three_wire_port.f)
rightLine = Line(brain.three_wire_port.e)

leftMotor = Motor(Ports.PORT11, GearSetting.RATIO_18_1, True)
rightMotor = Motor(Ports.PORT8, GearSetting.RATIO_18_1, True)

armMotor = Motor(Ports.PORT7, GearSetting.RATIO_18_1, False)
forkMotor = Motor(Ports.PORT6, GearSetting.RATIO_18_1, False)
basketMotor = Motor(Ports.PORT16, GearSetting.RATIO_18_1, False)

leftMotor.reset_position()
rightMotor.reset_position()
armMotor.reset_position()
forkMotor.reset_position()

forkMotor.set_stopping(HOLD)

# Vision
Vision16__LIME = Signature(1, -6571, -5693, -6132, -3053, -2661, -2857, 2.5, 0)
Vision16__GRAPEFRUIT = Signature(2, 3641, 5393, 4517, -2541, -2241, -2391, 2.5, 0)
Vision16__LEMON = Signature(3, 1519, 1965, 1742, -3595, -3365, -3480, 2.5, 0)
Vision16 = Vision(Ports.PORT16, 50, Vision16__LIME, Vision16__GRAPEFRUIT, Vision16__LEMON)
Vision3_LIME = Signature(1, -6429, -5309, -5869, -3997, -3303, -3650, 2.5, 0)
Vision3 = Vision(Ports.PORT20, 50, Vision3_LIME)

targetX = 0

# Line-following thresholds
lowerBound = 60
upperBound = 100

# Constants
wheelCircumference = 314.159265

# Main loop control
runMainFunction = False


# Vision Function
def detect():
    obj = Vision16.take_snapshot(Vision16__LIME)
    if obj:
        largest = Vision3.largest_object()
        cx, cy, width, height = largest.centerX, largest.centerY, largest.width, largest.height
        return cx, cy, width, height
    else:
        return None, None, 0, 0


# Line-following function
def lineFollow():
    if lowerBound <= leftLine.reflectivity() <= upperBound and lowerBound <= rightLine.reflectivity() <= upperBound:
        leftMotor.spin(FORWARD, 200)
        rightMotor.spin(FORWARD, -200)
    elif leftLine.reflectivity() > rightLine.reflectivity():
        leftMotor.spin(FORWARD, 170)
        rightMotor.spin(FORWARD, -90)
    elif rightLine.reflectivity() > leftLine.reflectivity():
        leftMotor.spin(FORWARD, 90)
        rightMotor.spin(FORWARD, -170)
    elif leftLine.reflectivity() < lowerBound and rightLine.reflectivity() < lowerBound:
        if leftLine.reflectivity() < rightLine.reflectivity():
            leftMotor.spin(FORWARD, 225)
            rightMotor.spin(FORWARD, -150)
        else:
            leftMotor.spin(FORWARD, 150)
            rightMotor.spin(FORWARD, -225)


# Fruit collection function
def collect(height):
    forkMotor.spin_to_position(0)
    forkMotor.reset_position()
    forkMotor.spin_to_position(-height, DEGREES, 200, RPM)

    leftMotor.spin_for(FORWARD, 700, DEGREES, 100, RPM, False)
    rightMotor.spin_for(FORWARD, -700, DEGREES, 100, RPM, True)

    forkMotor.spin_to_position(0)
    wait(1, SECONDS)

    leftMotor.spin_for(FORWARD, -720, DEGREES, 100, RPM, False)
    rightMotor.spin_for(FORWARD, 720, DEGREES, 100, RPM, True)


# Main function
def mainFunction():
    global currentState
    global targetX
    global i

    if currentState == IDLE:
        print("Starting autonomous sequence")
        basketMotor.spin_to_position(60, DEGREES)  # Reset basket position2
        currentState = LINE

    elif currentState == LINE:
        rotations = (2000 / wheelCircumference) * 360

        while True:
            leftPos = leftMotor.position()
            rightPos = rightMotor.position()

            if leftPos < rotations and rightPos < rotations and ultraSonic.distance(MM) >= 50:
                lineFollow()
            else:
                leftMotor.stop()
                rightMotor.stop()
                print("LINE -> SEARCHING")
                currentState = SEARCHING
                break

    elif currentState == SEARCHING:
        leftMotor.spin(FORWARD, -100)
        rightMotor.spin(FORWARD, -100)
        cx, cy, width, height = detect()
        if cx is not None:
            leftMotor.stop()
            rightMotor.stop()
            print("SEARCHING -> APPROACHING")
            currentState = APPROACHING
        else:
            print("Timeout reached, returning to LINE FOLLOWING")
            currentState = LINE

    elif currentState == APPROACHING:
        cx, cy, width, height = detect()
        if cx is None:
            print("APPROACHING -> SEARCHING")
            currentState = SEARCHING
        else:
            error = 255 - cx
            if height < 120:
                if error < -15:
                    leftMotor.spin(FORWARD, 90)
                    rightMotor.spin(FORWARD, -20)
                elif error > 15:
                    leftMotor.spin(FORWARD, 20)
                    rightMotor.spin(FORWARD, -90)
                else:
                    leftMotor.spin(FORWARD, 30)
                    rightMotor.spin(FORWARD, -30)
            else:
                print("APPROACHING -> COLLECTING")
                leftMotor.stop()
                rightMotor.stop()
                currentState = COLLECTING

    elif currentState == COLLECTING:
        #basketMotor.spin_to_position(150, DEGREES)  # Reset basket position
        collect(55)
        print("COLLECTING -> RETURNING")
        currentState = RETURNING

    elif currentState == RETURNING:
        # Step 1: Back up until detecting the line
        print("Backing up to find the line")
        while leftLine.reflectivity() < 50 and rightLine.reflectivity() < 50:
            leftMotor.spin(REVERSE, 150, RPM)
            rightMotor.spin(REVERSE, -150, RPM)

        leftMotor.stop()
        rightMotor.stop()
        print("Line detected")

        # Step 2: Line follow until 60 mm away from target
        print("Line following to drop-off point")
        while ultraSonic.distance(MM) > 60:
            lineFollow()

        leftMotor.stop()
        rightMotor.stop()
        print("At drop-off point")

        # Step 3: Deposit the fruit
        print("Depositing fruit into the box")
        basketMotor.spin_to_position(-65, DEGREES)  # Dump fruit
        wait(1, SECONDS)  # Pause to allow fruit to fall

        # Step 4: Line follow backwards to starting position
        print("Line following backwards to starting position")
        # Reset motor positions to track the distance back
        leftMotor.reset_position()
        rightMotor.reset_position()

        target_distance = leftMotor.position(DEGREES)  # Record the forward distance traveled

        while leftMotor.position(DEGREES) > -target_distance:
            if leftLine.reflectivity() > 50 and rightLine.reflectivity() > 50:
                leftMotor.spin(REVERSE, 150, RPM)
                rightMotor.spin(REVERSE, -150, RPM)
            elif leftLine.reflectivity() > rightLine.reflectivity():
                leftMotor.spin(REVERSE, 170, RPM)
                rightMotor.spin(REVERSE, -90, RPM)
            elif rightLine.reflectivity() > leftLine.reflectivity():
                leftMotor.spin(REVERSE, 90, RPM)
                rightMotor.spin(REVERSE, -170, RPM)
            else:
                leftMotor.spin(REVERSE, 150, RPM)
                rightMotor.spin(REVERSE, -150, RPM)

        leftMotor.stop()
        rightMotor.stop()
        print("Returned to starting position")

        # Transition back to LINE state
        currentState = LINE

    # elif currentState == RETURNING:
    #     # Step 1: Return to the line
    #     leftMotor.spin_for(REVERSE, 720, DEGREES, 35, RPM, False)
    #     rightMotor.spin_for(REVERSE, -720, DEGREES, 35, RPM, True)

    #     while leftLine.reflectivity() > 50 or rightLine.reflectivity() > 50:
    #         leftMotor.spin(FORWARD, 30)
    #         rightMotor.spin(FORWARD, -30)
        
    #     leftMotor.stop()
    #     rightMotor.stop()

    #     # Follow the line until both sensors detect it
    #     while leftLine.reflectivity() < 50 or rightLine.reflectivity() < 50:
    #         lineFollow()

    #     # Stop motors when the line is detected
    #     leftMotor.stop()
    #     rightMotor.stop()

    #     # Step 2: Deposit fruit in the box
    #     print("Depositing fruit into the box")
    #     basketMotor.spin_to_position(-65, DEGREES)  # Dump fruit
    #     wait(1, SECONDS)  # Pause for dumping

    #     # Step 3: Turn 180 degrees
    #     print("Turning 180 degrees")
    #     leftMotor.spin_for(FORWARD, 720, DEGREES, 50, RPM, False)  # 360 degrees * 2 for 180-degree turn
    #     rightMotor.spin_for(FORWARD, -720, DEGREES, 50, RPM, True)

    #     # Step 4: Transition back to LINE state
    #     print("RETURNING -> LINE")
    #     currentState = LINE


# Continuous loop for control
while True:
    if controller.buttonA.pressing():
        wait(0.3, SECONDS)  # Debounce to prevent multiple toggles
        runMainFunction = not runMainFunction

        if not runMainFunction:
            print("Stopping all motors")
            leftMotor.stop()
            rightMotor.stop()
            forkMotor.stop()
            armMotor.stop()
            currentState = IDLE
    


    if runMainFunction:
        mainFunction()
