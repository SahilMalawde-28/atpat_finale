import matplotlib.pyplot as plt
import numpy as np

# Benefit categories (excluding Early Warning)
categories = ['Community Awareness', 'Faster Response', 'Data-Driven Decisions', 'Resource Optimization', 'Ocean Safety']
N = len(categories)

# Example strength/presence values (0-10)
values = [8, 9, 7, 6, 10]
values += values[:1]  # Close the loop

# Compute angle for each category
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]

# Plot
fig, ax = plt.subplots(figsize=(6,6), subplot_kw=dict(polar=True))
ax.plot(angles, values, color='teal', linewidth=2, linestyle='solid')
ax.fill(angles, values, color='teal', alpha=0.25)

# Labels
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=10)
ax.set_yticks([2,4,6,8,10])
ax.set_yticklabels(['2','4','6','8','10'])
ax.set_title("Benefits of Shore", fontsize=16, fontweight='bold', pad=20)

plt.show()

