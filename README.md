
## Support EDMRN
Love EDMRN v1.0.5? Support its development with a coffee! ☕  
# [Buy me a coffee on Ko-fi](https://ko-fi.com/ninurtakalhu)  


# PLEASE DOWNLOAD LATEST VERSION!

# Elite Dangerous Explorer Route Optimizer

This tool optimizes long-range routes for Astrobiology and general exploration missions in Elite Dangerous. It uses a **Travelling Salesperson Problem (TSP)** solver (2-Opt Heuristic) to find the **shortest distance** route based on your ship's jump range.

This tool was developed by **CMDR Ninurta Kalhu** for personal exploration missions and is now shared with the Elite Dangerous community.

## 🚀 Features

- **Maximum Efficiency:** Significantly reduces total route distance, thereby minimizing the number of jumps required for your expedition.
- **Dynamic Range:** Prompts for your ship's jump range (LY) every time it runs and calculates the required number of jumps based on this range. (Default: 70.0 LY)
- **Flexible Start:** Provides the option to start the route from any system you choose or to find the overall shortest loop.
- **Ease of Use:** Runs with a single double-click on a `.bat` file.

## 🛠️ Setup

1.  **Python:** Ensure [Python 3.x](https://www.python.org/downloads/) is installed on your computer.
2.  **Download Files:** Download all files from this repository (`route_optimizer.py`, `Start.bat`, `requirements.txt`) into a single folder.
3.  **Data File:** Download a CSV file containing the **X, Y, Z coordinates** of the systems you wish to visit from a source like [Spansh Bodies Search](https://spansh.co.uk/bodies). Place the CSV file in your ED_Planner folder and run `Start.bat`.
4.  **Install Libraries:** Open CMD (Command Prompt) or PowerShell in the downloaded folder and run the following command to install the necessary libraries:
    ```bash
    pip install -r requirements.txt
    ```

## 🗺️ Usage Steps

1.  **Run:** Double-click the **`Start.bat`** file.
2.  **Range Input:** The program will ask for your ship's range. (e.g., enter `70.0` or leave blank to use the default).
3.  **Starting System Input:** The program will then ask for the system name you want to start the route from. (e.g., enter `Whamboi XU-W c15-3` or just press Enter to let it automatically find the **shortest loop route**).
4.  **Result:** Optimization completes in seconds, and the result CSV file is created in the same folder.

## 💾 Output

The optimized route is saved to a CSV file that includes the jump count and range in its name (e.g., `Optimized_Route_113_J605_M70.0LY.csv`). You can manually input this file's contents into the Elite Dangerous Galaxy Map to begin your journey.


Fly safe, Commander! O7

CMDR Ninurta Kalhu



