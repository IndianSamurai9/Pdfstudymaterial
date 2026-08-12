import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
import os
import random

# ---------- CONFIG ----------
PAGE_SIZE = (1240, 1754)  # A4
BG_COLOR = (252, 245, 235) # Cream paper
FONT_PATH = "Caveat.ttf"  # Download manually or use default

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        return ImageFont.load_default()

def draw_handwritten(draw, text, pos, size=40, color=(0,0,0), max_width=None):
    """Draw text with natural handwritten spacing (no rotation for speed)."""
    font = get_font(size)
    x, y = pos
    words = text.split(' ')
    line = ""
    for word in words:
        test_line = line + word + " "
        bbox = font.getbbox(test_line)
        if max_width and bbox[2] > max_width:
            draw.text((x, y), line, font=font, fill=color)
            y += size + 5
            line = word + " "
        else:
            line = test_line
    draw.text((x, y), line, font=font, fill=color)
    return y + size + 5

def render_gantt(data):
    """Generate Gantt chart as PIL Image."""
    processes = data['processes']
    arrivals = data['arrival']
    bursts = data['burst']
    colors = data['colors']
    
    fig, ax = plt.subplots(figsize=(10, 2.5))
    y_pos = 0.5
    current_time = 0
    sorted_idx = sorted(range(len(processes)), key=lambda i: arrivals[i])
    
    for idx in sorted_idx:
        p = processes[idx]
        arrival = arrivals[idx]
        burst = bursts[idx]
        if current_time < arrival:
            ax.barh(y_pos, arrival - current_time, left=current_time, color='lightgray', edgecolor='black', linestyle='dotted')
            ax.text(current_time + (arrival - current_time)/2, y_pos, "Idle", ha='center', va='center', fontsize=10)
            current_time = arrival
        ax.barh(y_pos, burst, left=current_time, color=colors[idx], edgecolor='black', linewidth=2)
        ax.text(current_time + burst/2, y_pos, f"{p} ({burst}ms)", ha='center', va='center', fontsize=12, fontweight='bold')
        current_time += burst
        y_pos += 1
    
    ax.set_xlabel("Time (ms)", fontsize=14)
    ax.set_yticks([])
    ax.set_xlim(0, max(current_time + 2, 10))
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    ax.set_title("CPU Scheduling (FCFS)", fontsize=16, fontweight='bold', pad=15)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    buf.seek(0)
    return Image.open(buf)

def render_pagetable(matrix):
    """Generate Page Table grid as PIL Image."""
    fig, ax = plt.subplots(figsize=(6, 3))
    rows, cols = len(matrix), len(matrix[0])
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_xticks([i+0.5 for i in range(cols)])
    ax.set_yticks([i+0.5 for i in range(rows)])
    ax.set_xticklabels([f"Page {i}" for i in range(cols)])
    ax.set_yticklabels([f"Frame {i}" for i in range(rows)])
    
    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            color = '#90EE90' if val == 1 else '#FF6B6B'
            rect = patches.Rectangle((j, rows-1-i), 1, 1, linewidth=2, edgecolor='black', facecolor=color)
            ax.add_patch(rect)
            status = "Valid" if val == 1 else "Invalid"
            ax.text(j+0.5, rows-1-i+0.5, status, ha='center', va='center', fontsize=12)
    
    ax.set_title("Page Table (Valid/Invalid Bits)", fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    buf.seek(0)
    return Image.open(buf)

def render_inode(data):
    """Generate Inode structure as PIL Image."""
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 3)
    ax.axis('off')
    y_base = 1.5
    
    # Direct
    for i, block in enumerate(data['direct'][:5]):
        rect = patches.Rectangle((i*1.2 + 0.5, y_base), 1, 0.8, linewidth=2, edgecolor='blue', facecolor='lightblue')
        ax.add_patch(rect)
        ax.text(i*1.2 + 1.0, y_base + 0.4, f"Direct {block}", ha='center', va='center', fontsize=10)
    
    # Single Indirect
    rect = patches.Rectangle((6.5, y_base), 0.8, 0.8, linewidth=2, edgecolor='red', facecolor='pink')
    ax.add_patch(rect)
    ax.text(6.9, y_base + 0.4, f"Single\n→{data['single_indirect']}", ha='center', va='center', fontsize=9)
    
    ax.set_title("Inode Pointer Structure", fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    buf.seek(0)
    return Image.open(buf)

def generate_pdf(data):
    """Assemble all components into a single PDF (return bytes)."""
    # Render diagrams
    gantt_img = render_gantt(data['gantt'])
    pt_img = render_pagetable(data['paging']['page_table'])
    inode_img = render_inode(data['inode'])
    
    # Create page
    page = Image.new('RGB', PAGE_SIZE, color=BG_COLOR)
    draw = ImageDraw.Draw(page)
    y_offset = 50
    
    # Title
    y_offset = draw_handwritten(draw, f"📘 {data['title']}", (50, y_offset), size=56, color=(10, 30, 120))
    y_offset += 20
    
    # Bullets
    for point in data['bullet_points']:
        y_offset = draw_handwritten(draw, f"• {point}", (80, y_offset), size=38, color=(30, 30, 30))
    y_offset += 30
    
    # Gantt
    gantt_resized = gantt_img.resize((900, 250))
    page.paste(gantt_resized, (150, y_offset))
    y_offset += 280
    
    # Page Table + Inode (side by side)
    pt_resized = pt_img.resize((500, 300))
    page.paste(pt_resized, (100, y_offset))
    inode_resized = inode_img.resize((550, 300))
    page.paste(inode_resized, (620, y_offset))
    
    # Save to bytes
    buf = io.BytesIO()
    page.save(buf, format='PDF', resolution=100.0)
    buf.seek(0)
    return buf.getvalue()
